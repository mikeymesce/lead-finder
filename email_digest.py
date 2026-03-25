"""
Email digest — sends top leads via Gmail SMTP.

Uses Gmail App Password (not regular password). Set up:
1. Enable 2FA on your Google account
2. Go to myaccount.google.com > Security > App passwords
3. Generate a password for "Mail"
4. Add to .env: GMAIL_ADDRESS and GMAIL_APP_PASSWORD

Only sends if it's been 3+ days since last email (configurable).
"""

import json
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


LAST_EMAIL_FILE = "last_email.json"


def _load_last_email():
    """Load the last email timestamp."""
    if not os.path.exists(LAST_EMAIL_FILE):
        return {}
    try:
        with open(LAST_EMAIL_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_last_email(data):
    """Save the last email timestamp."""
    with open(LAST_EMAIL_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _should_send(config):
    """
    Check if enough days have passed since last email.
    Returns (should_send: bool, reason: str).
    """
    freq = config.get("email", {}).get("frequency_days", 3)
    last = _load_last_email()
    last_sent = last.get("last_sent")

    if not last_sent:
        return True, "first email ever"

    try:
        last_date = datetime.strptime(last_sent, "%Y-%m-%d")
        days_since = (datetime.now() - last_date).days
        if days_since >= freq:
            return True, f"{days_since} days since last email"
        else:
            return False, f"only {days_since} day(s) since last email (need {freq})"
    except ValueError:
        return True, "couldn't parse last email date"


def _format_money(amount):
    """Format an integer as $XXX,XXX or empty string."""
    if amount is None:
        return "N/A"
    return f"${amount:,}"


def _format_ratio(ratio):
    """Format price-to-SDE ratio."""
    if ratio is None:
        return "N/A"
    return f"{ratio}x"


def _build_html(leads, date_str):
    """Build a clean HTML email with the top leads."""

    lead_rows = ""
    for i, lead in enumerate(leads, 1):
        signals = ", ".join(lead.get("distress_signals", [])) or "None detected"
        status_badge = ' <span style="background:#22c55e;color:white;padding:2px 6px;border-radius:3px;font-size:11px;">NEW</span>' if lead.get("status") == "new" else ""

        lead_rows += f"""
        <div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:12px;background:#fafafa;">
            <h3 style="margin:0 0 8px 0;color:#1f2937;">
                #{i}. {lead.get('company', 'Unknown')}{status_badge}
            </h3>
            <table style="font-size:14px;color:#374151;line-height:1.6;">
                <tr><td style="padding-right:12px;font-weight:600;">Location:</td><td>{lead.get('location', 'N/A')}</td></tr>
                <tr><td style="padding-right:12px;font-weight:600;">Industry:</td><td>{lead.get('industry', 'N/A')}</td></tr>
                <tr><td style="padding-right:12px;font-weight:600;">Asking Price:</td><td>{_format_money(lead.get('asking_price'))}</td></tr>
                <tr><td style="padding-right:12px;font-weight:600;">SDE/Cash Flow:</td><td>{_format_money(lead.get('cash_flow'))}</td></tr>
                <tr><td style="padding-right:12px;font-weight:600;">Price/SDE:</td><td>{_format_ratio(lead.get('price_to_sde_ratio'))}</td></tr>
                <tr><td style="padding-right:12px;font-weight:600;">Distress Signals:</td><td>{signals}</td></tr>
                <tr><td style="padding-right:12px;font-weight:600;">Score:</td><td>{lead.get('score', 0)}</td></tr>
                <tr><td style="padding-right:12px;font-weight:600;">Source:</td><td>{lead.get('source', 'N/A')}</td></tr>
            </table>
            <a href="{lead.get('url', '#')}" style="display:inline-block;margin-top:8px;color:#2563eb;font-weight:600;">View Listing →</a>
        </div>
        """

    html = f"""
    <html>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#1f2937;">
        <h2 style="color:#1f2937;border-bottom:2px solid #2563eb;padding-bottom:8px;">
            DealFlow — Top Leads for {date_str}
        </h2>
        {lead_rows}
        <p style="font-size:12px;color:#9ca3af;margin-top:20px;">
            Sent by DealFlow. To stop these emails, remove GMAIL_APP_PASSWORD from .env.
        </p>
    </body>
    </html>
    """
    return html


def send_email(leads, config):
    """
    Send top N leads as an HTML email digest via Gmail SMTP.

    Returns (sent: bool, message: str) so main.py can report status.
    Won't crash if credentials aren't set — just skips.
    """
    # Load credentials from .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not installed — try env vars directly

    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_address or not gmail_password:
        return False, "Gmail credentials not set in .env (GMAIL_ADDRESS / GMAIL_APP_PASSWORD) — skipping email"

    # Check if it's time to send
    email_config = config.get("email", {})
    should, reason = _should_send(config)
    if not should:
        return False, f"Email skipped: {reason}"

    # Get top N leads
    top_n = email_config.get("top_n", 3)
    to_addr = email_config.get("to", gmail_address)
    top_leads = leads[:top_n]

    if not top_leads:
        return False, "No leads to email"

    # Build the email
    date_str = datetime.now().strftime("%B %d, %Y")
    subject = f"DealFlow: Top {len(top_leads)} Leads — {date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = to_addr

    html = _build_html(top_leads, date_str)
    msg.attach(MIMEText(html, "html"))

    # Send via Gmail SMTP
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_address, gmail_password)
            server.sendmail(gmail_address, to_addr, msg.as_string())

        # Record that we sent
        _save_last_email({
            "last_sent": datetime.now().strftime("%Y-%m-%d"),
            "leads_sent": len(top_leads),
        })

        return True, f"Email sent to {to_addr} with {len(top_leads)} leads"

    except smtplib.SMTPAuthenticationError:
        return False, "Gmail auth failed — check GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env"
    except Exception as e:
        return False, f"Email failed: {e}"
