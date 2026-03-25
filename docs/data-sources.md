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

## Active (Phase 2)

### Google Maps (via Google Search)
- **How we search:** Playwright searches Google for "[industry] company near [city]" and parses the local pack + organic business results
- **Data available:** Company name, address, phone, website, Google rating, review count
- **Distress signals detected:**
  - Low Google rating (under 3.5 stars)
  - Very few reviews (under 10) for established businesses
  - No website listed
  - Review snippets mentioning "closed", "out of business", "new ownership", "went downhill", etc.
- **Cost:** $0 (Playwright scraping, no API)
- **Limits:** Google may CAPTCHA if too many searches. We use polite delays (3-6 sec between searches).
- **Config:** `maps_search_areas` and `maps_max_results_per_area` in config.json

## Planned (Phase 3)

- State business registrations
- Court records (divorce/estate filings)
