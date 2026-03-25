# DealFlow

Automated daily tool that finds small electrical and plumbing companies for sale in the tri-state area (NY/NJ/CT). Scores leads on deal quality and distress signals, deduplicates across runs, and emails you the top 3 every few days.

## What It Does

1. Scrapes business-for-sale marketplaces (BizBuySell, BizQuest, BusinessBroker.net)
2. Scrapes Google Maps for distressed businesses not listed for sale
3. Scores each lead: deal quality (SDE, price-to-SDE ratio) + distress signals + red flags
4. Deduplicates — tracks seen leads so you know what's new
5. Picks top 3 marketplace + top 3 Maps leads
6. Saves to Google Sheet (or local CSV)
7. Emails you the top 3 overall every 3 days

## Setup

### Requirements
- Python 3.8+
- pip

### Install
```bash
cd "web search tool"
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

### Google Sheets (optional but recommended)
See `docs/google-sheets-setup.md` for step-by-step instructions.

Without Google Sheets, results save to `leads.csv` locally.

### Email Digest (optional)
To get top leads emailed to you:
1. Enable 2-Factor Authentication on your Google account
2. Go to myaccount.google.com > Security > App passwords
3. Generate a password for "Mail"
4. Add to `.env`:
   ```
   GMAIL_ADDRESS=you@gmail.com
   GMAIL_APP_PASSWORD=your-app-password
   ```

Emails send every 3 days (configurable in `config.json`).

### Run
```bash
python3 main.py              # Full run + email
python3 main.py --no-email   # Skip email
python3 main.py --maps-only  # Only Google Maps
python3 main.py --marketplace-only  # Only marketplace listings
```

### Run Daily (automatic)
See `docs/architecture.md` for cron setup instructions.

## Search Criteria

Edit `config.json` to change:
- Industries (default: plumbing, electrical)
- States (default: NY, NJ, CT)
- Employee range (default: 4-40)
- Profit/SDE range (default: $100K-$1M)
- Asking price max (default: $5M)
- Scoring weights
- Email settings

## Skip List

Add URLs to `skip_list.json` to permanently hide companies you're not interested in:
```json
["https://example.com/listing-123", "https://example.com/listing-456"]
```
