# Architecture

## File Map

```
web search tool/
├── main.py              # Entry point — run this (supports --maps-only, --marketplace-only)
├── config.json          # Search criteria (edit this to change filters)
├── scraper.py           # Phase 1: Scrapes business-for-sale marketplaces
├── maps_scraper.py      # Phase 2: Scrapes Google Maps for distressed businesses
├── filters.py           # Filters + scores results from both scrapers
├── output.py            # Writes to CSV and/or Google Sheets
├── requirements.txt     # Python dependencies
├── .env                 # API keys (not in git)
├── .gitignore
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
4. `filters.py` scores all results from both scrapers (distress keywords, rating, data completeness)
5. `output.py` picks the top N results and appends to Google Sheet (or CSV)

## Data Flow

```
BizBuySell ─┐
BizQuest ───┤──> scraper.py ────────┐
BBN ────────┘                       ├──> filters.py ──> output.py ──> Google Sheet
                                    │                             └──> leads.csv
Google Maps ──> maps_scraper.py ────┘
```

## CLI Flags

- `python3 main.py` — Run both scrapers
- `python3 main.py --marketplace-only` — Only marketplace listings
- `python3 main.py --maps-only` — Only Google Maps businesses

## Running Daily

To run automatically every day at 8am:

```bash
crontab -e
```

Add this line:
```
0 8 * * * cd "/Users/michaelmesce/Desktop/web search tool" && /usr/bin/python3 main.py
```
