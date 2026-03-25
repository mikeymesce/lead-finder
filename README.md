# Lead Finder

Automated daily scraper that finds small electrical and plumbing companies for sale in the tri-state area (NY/NJ/CT). Prioritizes distressed sales (retirement, divorce, death, motivated sellers).

## What It Does

1. Scrapes business-for-sale marketplaces (BizBuySell, BizQuest, BusinessBroker.net)
2. Filters for plumbing & electrical companies, 4-40 employees, tri-state area
3. Flags distress signals in listing descriptions
4. Logs the top 1-2 matches to a Google Sheet (or local CSV)

## Setup

### Requirements
- Python 3.8+
- pip

### Install
```bash
cd "web search tool"
pip install -r requirements.txt
```

### Google Sheets (optional but recommended)
See `docs/google-sheets-setup.md` for step-by-step instructions.

Without Google Sheets, results save to `leads.csv` locally.

### Run
```bash
python3 main.py
```

### Run Daily (automatic)
See `docs/architecture.md` for cron setup instructions.

## Search Criteria

Edit `config.json` to change:
- Industries (default: plumbing, electrical)
- States (default: NY, NJ, CT)
- Employee range (default: 4-40)
- Profit/SDE range (default: $100K-$1M)
- Distress keywords
