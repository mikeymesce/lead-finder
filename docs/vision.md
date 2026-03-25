# Vision

## Goal

Find 1-2 acquisition targets per day — small plumbing and electrical companies in the tri-state area (NY/NJ/CT) that are likely distressed sales.

## Target Profile

- **Industry:** Plumbing, Electrical
- **Employees:** 4–40
- **Profit (SDE):** $100K–$1M
- **Location:** New York, New Jersey, Connecticut
- **Priority signals:** Retirement, divorce, death/estate, motivated seller, health issues

## Phases

### Phase 1 (complete) — Free Scraper
- Scrape business-for-sale marketplaces (BizBuySell, BizQuest, BusinessBroker.net)
- Filter by criteria above
- Flag distress keywords
- Log to Google Sheet / CSV

### Phase 2 (current) — Google Maps Distress Finder
- Google Maps scraper finds plumbing/electrical companies NOT listed for sale
- Searches 10 tri-state metro areas for both industries (20 searches total)
- Detects distress signals: low rating, few reviews, no website, negative review keywords
- $0 cost — Playwright scraping, no paid APIs
- Run with `--maps-only` or combined with Phase 1

### Phase 3 (future) — Outreach
- Auto-generate personalized outreach letters
- Track which companies you've contacted
- Follow-up reminders
