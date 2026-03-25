"""
Outputs leads to CSV, Google Sheets, and manages deduplication.

Tracks seen leads in seen_leads.json to mark new vs returning results.
Respects skip_list.json to permanently hide unwanted leads.
Enforces separate quotas for marketplace (3) and Maps (3) sources.
"""

import csv
import json
import os
from datetime import datetime


CSV_FILE = "leads.csv"
SEEN_FILE = "seen_leads.json"
SKIP_FILE = "skip_list.json"

CSV_HEADERS = [
    "Date", "Company", "Industry", "Location", "Employees",
    "Asking Price", "Revenue", "Cash Flow/SDE", "Price/SDE",
    "Distress Signals", "Score", "Deal Quality", "Distress Score",
    "Red Flags", "Source", "URL", "Status", "Days Listed"
]


# ---------------------------------------------------------------------------
# Money formatting
# ---------------------------------------------------------------------------

def _format_money(amount):
    """Format an integer as $XXX,XXX or empty string."""
    if amount is None:
        return ""
    return f"${amount:,}"


def _format_ratio(ratio):
    """Format price-to-SDE ratio as '2.5x' or empty string."""
    if ratio is None:
        return ""
    return f"{ratio}x"


# ---------------------------------------------------------------------------
# Deduplication — seen_leads.json
# ---------------------------------------------------------------------------

def _load_seen():
    """Load the seen leads tracker. Returns dict keyed by URL."""
    if not os.path.exists(SEEN_FILE):
        return {}
    try:
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_seen(seen):
    """Write the seen leads tracker back to disk."""
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=2)


def _update_seen(leads, seen):
    """
    Update the seen tracker with today's leads.
    Marks each lead as 'new' or 'seen' and calculates listing_age.
    Returns the updated seen dict.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    for lead in leads:
        url = lead.get("url", "")
        if not url:
            lead["status"] = "new"
            lead["listing_age"] = 0
            continue

        if url in seen:
            # Previously seen — update last_seen
            seen[url]["last_seen"] = today
            lead["status"] = "seen"
            # Calculate days since first seen
            try:
                first = datetime.strptime(seen[url]["first_seen"], "%Y-%m-%d")
                lead["listing_age"] = (datetime.now() - first).days
            except (ValueError, KeyError):
                lead["listing_age"] = 0
        else:
            # Brand new lead
            seen[url] = {
                "url": url,
                "company": lead.get("company", ""),
                "first_seen": today,
                "last_seen": today,
                "status": "new",
            }
            lead["status"] = "new"
            lead["listing_age"] = 0

    return seen


# ---------------------------------------------------------------------------
# Skip list — skip_list.json
# ---------------------------------------------------------------------------

def _load_skip_list():
    """Load URLs to permanently skip."""
    if not os.path.exists(SKIP_FILE):
        return []
    try:
        with open(SKIP_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _apply_skip_list(leads, skip_urls):
    """Remove any leads whose URL is in the skip list."""
    if not skip_urls:
        return leads
    skip_set = set(skip_urls)
    filtered = [l for l in leads if l.get("url", "") not in skip_set]
    skipped = len(leads) - len(filtered)
    if skipped:
        print(f"Skipped {skipped} leads from skip list")
    return filtered


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def save_to_csv(leads):
    """Append leads to the local CSV file."""
    file_exists = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(CSV_HEADERS)

        today = datetime.now().strftime("%Y-%m-%d")

        for lead in leads:
            writer.writerow([
                today,
                lead.get("company", ""),
                lead.get("industry", ""),
                lead.get("location", ""),
                lead.get("employees", ""),
                _format_money(lead.get("asking_price")),
                _format_money(lead.get("revenue")),
                _format_money(lead.get("cash_flow")),
                _format_ratio(lead.get("price_to_sde_ratio")),
                ", ".join(lead.get("distress_signals", [])),
                lead.get("score", 0),
                lead.get("deal_quality_score", 0),
                lead.get("distress_score", 0),
                ", ".join(lead.get("red_flags", [])),
                lead.get("source", ""),
                lead.get("url", ""),
                lead.get("status", "new"),
                lead.get("listing_age", 0),
            ])

    print(f"Saved {len(leads)} leads to {CSV_FILE}")


# ---------------------------------------------------------------------------
# Google Sheets output
# ---------------------------------------------------------------------------

def save_to_sheets(leads):
    """Append leads to Google Sheet. Returns True if successful, False otherwise."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        from dotenv import load_dotenv

        load_dotenv()
        sheet_id = os.getenv("GOOGLE_SHEET_ID")

        if not sheet_id:
            print("No GOOGLE_SHEET_ID in .env — skipping Google Sheets")
            return False

        if not os.path.exists("service-account.json"):
            print("No service-account.json found — skipping Google Sheets")
            return False

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file("service-account.json", scopes=scopes)
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(sheet_id).sheet1

        today = datetime.now().strftime("%Y-%m-%d")

        rows = []
        for lead in leads:
            rows.append([
                today,
                lead.get("company", ""),
                lead.get("industry", ""),
                lead.get("location", ""),
                str(lead.get("employees", "")),
                _format_money(lead.get("asking_price")),
                _format_money(lead.get("revenue")),
                _format_money(lead.get("cash_flow")),
                _format_ratio(lead.get("price_to_sde_ratio")),
                ", ".join(lead.get("distress_signals", [])),
                str(lead.get("score", 0)),
                str(lead.get("deal_quality_score", 0)),
                str(lead.get("distress_score", 0)),
                ", ".join(lead.get("red_flags", [])),
                lead.get("source", ""),
                lead.get("url", ""),
                lead.get("status", "new"),
                str(lead.get("listing_age", 0)),
            ])

        if rows:
            sheet.append_rows(rows)
            print(f"Added {len(rows)} leads to Google Sheet")

        return True

    except ImportError:
        print("Google Sheets libraries not installed — run: pip install gspread google-auth")
        return False
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return False


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def save_leads(leads):
    """
    Save leads to CSV and Google Sheets.
    Handles deduplication and skip list before saving.
    Returns the final list of leads (for email module to use).
    """
    if not leads:
        print("No leads to save today.")
        return []

    # Load skip list and remove unwanted leads
    skip_urls = _load_skip_list()
    leads = _apply_skip_list(leads, skip_urls)

    if not leads:
        print("All leads were in the skip list. Nothing to save.")
        return []

    # Update seen tracker — marks each lead as new/seen, calculates age
    seen = _load_seen()
    seen = _update_seen(leads, seen)
    _save_seen(seen)

    new_count = sum(1 for l in leads if l.get("status") == "new")
    seen_count = len(leads) - new_count
    print(f"Leads: {new_count} new, {seen_count} previously seen")

    # Save to CSV (always)
    save_to_csv(leads)

    # Try Google Sheets
    save_to_sheets(leads)

    return leads
