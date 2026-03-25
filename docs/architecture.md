# Architecture

## File Map

```
web search tool/
├── main.py              # Entry point — run this
├── config.json          # Search criteria (edit this to change filters)
├── scraper.py           # Scrapes all business-for-sale sites
├── filters.py           # Filters + scores results
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

1. `main.py` loads `config.json` for search criteria
2. `scraper.py` hits each business-for-sale site, parses listings
3. `filters.py` scores each listing (employee count, location, distress keywords)
4. `output.py` picks the top 1-2 results and appends to Google Sheet (or CSV)

## Data Flow

```
BizBuySell ─┐
BizQuest ───┤──> scraper.py ──> filters.py ──> output.py ──> Google Sheet
BBN ────────┘                                            └──> leads.csv
```

## Running Daily

To run automatically every day at 8am:

```bash
crontab -e
```

Add this line:
```
0 8 * * * cd "/Users/michaelmesce/Desktop/web search tool" && /usr/bin/python3 main.py
```
