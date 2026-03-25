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

### Phase 1 (current) — Free Scraper
- Scrape business-for-sale marketplaces (BizBuySell, BizQuest, BusinessBroker.net)
- Filter by criteria above
- Flag distress keywords
- Log to Google Sheet / CSV

### Phase 2 (future) — Enrichment
- Google Maps to find plumbing/electrical companies NOT listed for sale
- Enrich with public data (years in business, reviews declining, owner age)
- Cross-reference with court records for divorce/estate filings
- Requires small API budget (~$20-50/mo)

### Phase 3 (future) — Outreach
- Auto-generate personalized outreach letters
- Track which companies you've contacted
- Follow-up reminders
