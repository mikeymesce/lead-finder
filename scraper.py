"""
Scrapes business-for-sale listings via Google Search + Playwright.

We search Google with site: operators to find listings on BizBuySell,
BizQuest, and BusinessBroker.net, then parse the snippets for key data.
Direct scraping of these sites is blocked by their bot protection.
"""

import re
import time
import random
from playwright.sync_api import sync_playwright


def _polite_delay(min_sec=2, max_sec=4):
    """Wait between requests to avoid getting flagged."""
    time.sleep(random.uniform(min_sec, max_sec))


def _parse_money(text):
    """Parse strings like '$500,000' or '$1.2M' into integers."""
    if not text:
        return None
    text = text.strip().replace(",", "").replace("$", "").lower()
    if "m" in text:
        try:
            return int(float(text.replace("m", "")) * 1_000_000)
        except ValueError:
            return None
    if "k" in text:
        try:
            return int(float(text.replace("k", "")) * 1_000)
        except ValueError:
            return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _launch_browser(playwright):
    """Launch a Chromium browser with anti-detection settings."""
    browser = playwright.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    )
    page = context.new_page()
    page.add_init_script(
        'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    )
    return browser, context, page


def _google_search(page, query, num_results=20):
    """
    Run a Google search and return a list of results.
    Each result: {title, url, snippet}
    """
    from bs4 import BeautifulSoup

    encoded_query = query.replace(" ", "+")
    url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"

    try:
        page.goto(url, timeout=30000, wait_until="networkidle")
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f"  [ERROR] Google search failed: {e}")
        return []

    html = page.content()

    # Check for captcha
    if "captcha" in html.lower() or "unusual traffic" in html.lower():
        print("  [WARNING] Google CAPTCHA detected — too many searches. Try again later.")
        return []

    soup = BeautifulSoup(html, "html.parser")
    results = []

    for h3 in soup.find_all("h3"):
        parent_a = h3.find_parent("a")
        if not parent_a or not parent_a.get("href", "").startswith("http"):
            continue

        result_url = parent_a["href"]
        title = h3.get_text(strip=True)

        # Walk up to get the enclosing result container
        result_div = h3
        for _ in range(8):
            if result_div.parent:
                result_div = result_div.parent

        full_text = result_div.get_text(" ", strip=True)
        snippet = full_text.replace(title, "").strip()[:500]

        results.append({
            "title": title,
            "url": result_url,
            "snippet": snippet,
        })

    return results


def _clean_company_name(name):
    """Remove Google junk from company names."""
    # Remove BizBuySell/BizQuest URL breadcrumbs
    name = re.sub(r"BizBuySell\s*https?://.*?›.*?results?\s*", "", name)
    name = re.sub(r"BizQuest\s*https?://.*?›.*?results?\s*", "", name)
    name = re.sub(r"BusinessBroker.*?›.*?results?\s*", "", name)
    name = re.sub(r"https?://\S+", "", name)
    name = re.sub(r"›[^›]*", "", name)
    name = re.sub(r"\d+\s*results?\s*", "", name)
    # Remove trailing pipes, dots, dashes
    name = re.sub(r"[\s|·\-–—]+$", "", name)
    name = re.sub(r"^[\s|·\-–—]+", "", name)
    # Remove "Browse X" prefix
    name = re.sub(r"^Browse\s+\d+\s+", "", name)
    return name.strip()


def _parse_listing_from_google(result, search_type):
    """
    Parse a Google search result into a listing dict.
    Extracts what we can from the title and snippet.
    """
    title = result["title"]
    snippet = result["snippet"]
    url = result["url"]
    combined = f"{title} {snippet}".lower()

    listing = {
        "company": _clean_company_name(title),
        "url": url,
        "description": snippet,
        "location": "",
        "asking_price": None,
        "revenue": None,
        "cash_flow": None,
        "employees": None,
        "industry": search_type,
        "source": _detect_source(url),
    }

    # Skip category/index pages — we want individual listings
    # Category pages have titles like "Plumbing Businesses For Sale in..."
    if "businesses for sale" in title.lower() and "for sale in" in title.lower():
        # But they may contain listing previews in snippets
        # Try to extract individual listings from the snippet
        return _extract_listings_from_category_snippet(result, search_type)

    # Extract location from title or snippet
    state_patterns = [
        r"new york|NY|new jersey|NJ|connecticut|CT",
        r"nassau|suffolk|westchester|bergen|queens|brooklyn|manhattan|bronx|staten island",
        r"fairfield|hartford|new haven|middlesex|stamford|bridgeport",
    ]
    for pattern in state_patterns:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            listing["location"] = match.group()
            break

    # Extract asking price
    price_match = re.search(r"\$[\d,]+(?:\.\d+)?(?:[MmKk])?", snippet)
    if price_match:
        listing["asking_price"] = _parse_money(price_match.group())

    # Extract cash flow / SDE
    cf_match = re.search(
        r"(?:cash\s*flow|sde|seller.*discretionary)[:\s]*\$?([\d,]+(?:\.\d+)?[MmKk]?)",
        combined,
    )
    if cf_match:
        listing["cash_flow"] = _parse_money(cf_match.group(1))

    # Extract revenue
    rev_match = re.search(
        r"(?:revenue|gross)[:\s]*\$?([\d,]+(?:\.\d+)?[MmKk]?)",
        combined,
    )
    if rev_match:
        listing["revenue"] = _parse_money(rev_match.group(1))

    # Extract employee count
    emp_match = re.search(r"(\d+)\s*(?:employees|staff|workers|techs|technicians)", combined)
    if emp_match:
        listing["employees"] = int(emp_match.group(1))

    return [listing]


def _extract_listings_from_category_snippet(result, search_type):
    """
    Category page snippets often contain previews of individual listings.
    Try to split them out.
    """
    snippet = result["snippet"]
    url = result["url"]

    # Look for individual listing patterns in the snippet
    # These often appear as "Company Name · $XXX,XXX. Cash Flow: $XXX"
    listings = []

    # Split on common separators
    parts = re.split(r";\s*|Read more", snippet)
    for part in parts:
        part = part.strip()
        if not part or len(part) < 20:
            continue

        # Must contain a dollar amount to be a listing
        if "$" not in part:
            continue

        listing = {
            "company": "",
            "url": url,
            "description": part,
            "location": "",
            "asking_price": None,
            "revenue": None,
            "cash_flow": None,
            "employees": None,
            "industry": search_type,
            "source": _detect_source(url),
        }

        # Try to extract company name (text before the first $)
        name_match = re.match(r"^(.*?)\s*[\$·]", part)
        if name_match:
            name = name_match.group(1).strip().strip("·").strip()
            # Clean up junk from name
            name = re.sub(r"^[\d]+\s*results?\s*", "", name)
            name = re.sub(r"^Browse\s+\d+\s+", "", name)
            name = _clean_company_name(name)
            if len(name) > 5:
                listing["company"] = name

        # Extract prices
        prices = re.findall(r"\$([\d,]+(?:\.\d+)?[MmKk]?)", part)
        if prices:
            listing["asking_price"] = _parse_money(prices[0])
        if len(prices) > 1:
            listing["cash_flow"] = _parse_money(prices[1])

        # Extract cash flow specifically labeled
        cf_match = re.search(r"cash\s*flow[:\s]*\$?([\d,]+)", part, re.IGNORECASE)
        if cf_match:
            listing["cash_flow"] = _parse_money(cf_match.group(1))

        # Location from the category page title
        loc_match = re.search(
            r"(?:new york|new jersey|connecticut|nassau|suffolk|westchester|bergen|queens)",
            result["title"],
            re.IGNORECASE,
        )
        if loc_match:
            listing["location"] = loc_match.group()

        if listing["company"]:
            listings.append(listing)

    return listings


def _detect_source(url):
    """Detect which marketplace a URL belongs to."""
    if "bizbuysell.com" in url:
        return "BizBuySell"
    elif "bizquest.com" in url:
        return "BizQuest"
    elif "businessbroker.net" in url:
        return "BusinessBroker.net"
    elif "loopnet.com" in url:
        return "LoopNet"
    else:
        return "Google"


# ---------------------------------------------------------------------------
# Search queries — what we actually search Google for
# ---------------------------------------------------------------------------

SEARCH_QUERIES = [
    # BizBuySell — plumbing
    'site:bizbuysell.com plumbing business for sale "new york" OR "new jersey" OR "connecticut"',
    # BizBuySell — electrical
    'site:bizbuysell.com electrical OR "electrical contracting" business for sale "new york" OR "new jersey" OR "connecticut"',
    # BizQuest — plumbing + electrical
    'site:bizquest.com plumbing OR electrical business for sale "new york" OR "new jersey" OR "connecticut"',
    # BusinessBroker.net
    'site:businessbroker.net plumbing OR electrical "new york" OR "new jersey" OR "connecticut"',
    # Distressed-specific search across all sites
    'plumbing OR electrical business for sale "new york" OR "new jersey" OR "connecticut" retiring OR "must sell" OR motivated OR divorce',
]


def scrape_all():
    """Run all Google searches and return combined listings."""
    all_listings = []

    print("Starting browser...")
    with sync_playwright() as p:
        browser, context, page = _launch_browser(p)

        for i, query in enumerate(SEARCH_QUERIES):
            print(f"\nSearch {i + 1}/{len(SEARCH_QUERIES)}: {query[:80]}...")
            _polite_delay(3, 6)

            results = _google_search(page, query, num_results=20)
            print(f"  Google returned {len(results)} results")

            for result in results:
                # Determine industry from search query
                if "plumbing" in query.lower() and "electrical" not in query.lower():
                    search_type = "Plumbing"
                elif "electrical" in query.lower() and "plumbing" not in query.lower():
                    search_type = "Electrical"
                else:
                    search_type = "Plumbing/Electrical"

                listings = _parse_listing_from_google(result, search_type)
                all_listings.extend(listings)

        browser.close()

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for listing in all_listings:
        if listing["url"] not in seen_urls:
            seen_urls.add(listing["url"])
            unique.append(listing)

    print(f"\nTotal unique listings found: {len(unique)}")
    return unique
