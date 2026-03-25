# Changelog

## 2026-03-25
- **Renamed to Public Deal Flow** (was "Lead Finder")
- New scoring model: deal quality (SDE range, price-to-SDE ratio) + distress signals (keyword groups with weights) + red flags (no financials, legal issues)
- Deduplication: tracks all seen leads in `seen_leads.json`, marks new vs returning
- Skip list: add URLs to `skip_list.json` to permanently hide leads
- Separate quotas: 3 marketplace + 3 Maps leads per run (6 total)
- Price-to-SDE ratio calculated and shown in output
- Email digest: sends top 3 leads via Gmail every 3 days (`email_digest.py`)
- Asking price max raised to $5M
- Updated all CSV/Sheet headers with new columns
- Created `.env.example` with all env vars
- Updated all docs

## 2026-03-24
- Project created
- Scaffolded docs: README, CLAUDE.md, architecture, vision, data sources, Google Sheets setup
- Built Phase 1 scraper: BizBuySell, BizQuest, BusinessBroker.net
- Config-driven search criteria (config.json)
- Distress keyword flagging
- Output to CSV (Google Sheets integration ready)
