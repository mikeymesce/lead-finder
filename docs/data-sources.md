# Data Sources

## Active (Phase 1)

### BizBuySell
- **URL:** https://www.bizbuysell.com
- **What:** Largest business-for-sale marketplace in the US
- **How we search:** Scrape search results filtered by industry + location
- **Data available:** Asking price, revenue, cash flow, employees, description
- **Limits:** May block excessive requests. We add delays between requests.

### BizQuest
- **URL:** https://www.bizquest.com
- **What:** Business-for-sale listings, owned by BizBuySell
- **How we search:** Scrape search results filtered by category + state
- **Data available:** Similar to BizBuySell
- **Limits:** Same anti-scraping concerns

### BusinessBroker.net
- **URL:** https://www.businessbroker.net
- **What:** Independent business-for-sale marketplace
- **How we search:** Scrape listings by industry + state
- **Data available:** Asking price, cash flow, description
- **Limits:** Smaller inventory than BizBuySell

## Planned (Phase 2)

- Google Maps API (find companies not listed for sale)
- State business registrations
- Court records (divorce/estate filings)
