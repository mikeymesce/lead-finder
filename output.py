"""
Outputs leads to CSV and optionally Google Sheets.
"""

import csv
import os
from datetime import datetime


CSV_FILE = "leads.csv"
CSV_HEADERS = [
    "Date", "Company", "Industry", "Location", "Employees",
    "Asking Price", "Revenue", "Cash Flow / SDE", "Distress Signals",
    "Score", "Source", "URL"
]


def _format_money(amount):
    """Format an integer as $XXX,XXX or empty string."""
    if amount is None:
        return ""
    return f"${amount:,}"


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
                ", ".join(lead.get("distress_signals", [])),
                lead.get("score", 0),
                lead.get("source", ""),
                lead.get("url", ""),
            ])

    print(f"Saved {len(leads)} leads to {CSV_FILE}")


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
                ", ".join(lead.get("distress_signals", [])),
                str(lead.get("score", 0)),
                lead.get("source", ""),
                lead.get("url", ""),
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


def save_leads(leads):
    """Save leads to both CSV and Google Sheets."""
    if not leads:
        print("No leads to save today.")
        return

    # Always save to CSV as backup
    save_to_csv(leads)

    # Try Google Sheets
    save_to_sheets(leads)
