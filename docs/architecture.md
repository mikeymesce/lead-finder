# Architecture

## File Map

```
web search tool/
├── main.py              # Entry point — run this (--maps-only, --marketplace-only, --no-email)
├── config.json          # Search criteria, scoring weights, email settings
├── scraper.py           # Phase 1: Scrapes business-for-sale marketplaces
├── maps_scraper.py      # Phase 2: Scrapes Google Maps for distressed businesses
├── filters.py           # Filters + scores results (deal quality, distress, red flags)
├── output.py            # CSV/Sheets output, deduplication, skip list
├── email_digest.py      # Gmail email digest of top leads
├── requirements.txt     # Python dependencies
├── .env                 # API keys + Gmail credentials (not in git)
├── .env.example         # Template for .env
├── .gitignore
├── seen_leads.json      # Tracks every lead URL we've found (not in git)
├── skip_list.json       # URLs to permanently hide (not in git)
├── last_email.json      # Tracks when last email was sent (not in git)
├── docs/
│   ├── architecture.md      # This file
│   ├── vision.md            # Roadmap
│   ├── data-sources.md      # What sites we scrape
│   └── google-sheets-setup.md  # How to connect Google Sheets
├── CLAUDE.md
├── CHANGELOG.md
└── README.md
```

## How It Works

1. `main.py` loads `config.json` for search criteria and parses flags
2. `scraper.py` (Phase 1) searches Google for marketplace listings (BizBuySell, etc.)
3. `maps_scraper.py` (Phase 2) searches Google for Maps business results, detects distress signals
4. `filters.py` scores all results using three-part model:
   - **Deal Quality:** SDE in range, price-to-SDE ratio
   - **Distress:** keyword groups (death/estate, divorce, retiring, health, motivated, relocating) + Maps signals
   - **Red Flags:** no financials, legal keywords (negative score)
5. `output.py` deduplicates (via `seen_leads.json`), applies skip list, picks top 3 marketplace + top 3 Maps, saves to CSV/Sheets
6. `email_digest.py` sends top 3 overall via Gmail SMTP (every 3 days)

## Data Flow

```
BizBuySell ─┐
BizQuest ───┤──> scraper.py ────────┐
BBN ────────┘                       ├──> filters.py ──> output.py ──> Google Sheet
                                    │        │                    └──> leads.csv
Google Maps ──> maps_scraper.py ────┘        │                    └──> seen_leads.json
                                             │
                                             └──> email_digest.py ──> Gmail
```

## CLI Flags

- `python3 main.py` — Run both scrapers + email
- `python3 main.py --marketplace-only` — Only marketplace listings
- `python3 main.py --maps-only` — Only Google Maps businesses
- `python3 main.py --no-email` — Skip email digest

## Running Daily

To run automatically every day at 8am:

```bash
crontab -e
```

Add this line:
```
0 8 * * * cd "/Users/michaelmesce/Desktop/web search tool" && /usr/bin/python3 main.py >> cron.log 2>&1
```
