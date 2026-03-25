"""
Google Maps scraper — finds plumbing/electrical companies NOT listed for sale.

Searches Google Maps via regular Google search (to avoid Maps bot detection),
extracts business details, and flags distress signals like low ratings,
few reviews, no website, or concerning review snippets.

Phase 2 of the lead finder. $0 cost — uses Playwright only.
"""

import re
import time
import random
import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def _polite_delay(min_sec=2, max_sec=4):
    """Wait between requests to avoid getting flagged."""
    time.sleep(random.uniform(min_sec, max_sec))


def _load_config():
    """Load config.json."""
    with open("config.json", "r") as f:
        return json.load(f)


def _launch_browser(playwright):
    """Launch a Chromium browser with anti-detection settings.
    Same setup as scraper.py for consistency."""
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


# ---------------------------------------------------------------------------
# Google Search approach (more reliable than scraping Maps directly)
# ---------------------------------------------------------------------------

def _google_search_maps(page, query, max_results=10):
    """
    Search Google for a Maps-style query and extract the local business
    results (the "local pack" and organic results with business info).

    Returns a list of dicts with whatever we can extract:
      {name, address, phone, website, rating, review_count, snippet}
    """
    encoded = query.replace(" ", "+")
    url = f"https://www.google.com/search?q={encoded}&num=20"

    try:
        page.goto(url, timeout=30000, wait_until="networkidle")
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f"  [ERROR] Google search failed: {e}")
        return []

    html = page.content()

    # Check for captcha
    if "captcha" in html.lower() or "unusual traffic" in html.lower():
        print("  [WARNING] Google CAPTCHA detected. Try again later.")
        return []

    soup = BeautifulSoup(html, "html.parser")
    businesses = []

    # --- Strategy 1: Parse the local pack (map results) ---
    # Google's local pack uses divs with data-attrid or specific class patterns.
    # We look for business cards that contain ratings and addresses.
    _parse_local_pack(soup, businesses)

    # --- Strategy 2: Parse organic results for business info ---
    _parse_organic_results(soup, businesses)

    # Deduplicate by name (case-insensitive)
    seen = set()
    unique = []
    for b in businesses:
        key = b["name"].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(b)

    return unique[:max_results]


def _parse_local_pack(soup, businesses):
    """
    Extract businesses from Google's local pack (map results).
    These appear as a group of ~3 businesses with ratings, addresses, etc.
    """
    # Local pack entries often live in divs with role="heading" level 3
    # or within the maps widget. We look for patterns with star ratings.

    # Find all text blocks that look like local business entries.
    # Pattern: business name near a rating like "4.2" and "(123)" review count
    for div in soup.find_all("div"):
        text = div.get_text(" ", strip=True)

        # Look for the rating pattern: "X.X (NNN)" or "X.X(NNN)"
        rating_match = re.search(r"(\d\.\d)\s*\((\d[\d,]*)\)", text)
        if not rating_match:
            continue

        # This div likely contains a business. But skip if it's too big
        # (parent containers will also match).
        if len(text) > 500:
            continue

        rating = float(rating_match.group(1))
        review_count = int(rating_match.group(2).replace(",", ""))

        # Extract the business name — usually the first bold/heading text
        name = ""
        heading = div.find(["h3", "span", "div"], attrs={"role": "heading"})
        if heading:
            name = heading.get_text(strip=True)
        else:
            # Take text before the rating
            pre_rating = text[:rating_match.start()].strip()
            # Last "sentence" before rating is usually the name
            parts = re.split(r"[·|]", pre_rating)
            name = parts[-1].strip() if parts else pre_rating

        if not name or len(name) < 3:
            continue

        # Extract address — look for patterns with street/city/state
        address = ""
        addr_match = re.search(
            r"(\d+\s+[A-Za-z\s]+(?:St|Ave|Blvd|Rd|Dr|Ln|Way|Ct|Pl|Pkwy|Hwy)\.?[^·]*)",
            text, re.IGNORECASE
        )
        if addr_match:
            address = addr_match.group(1).strip()[:100]

        # Extract phone number
        phone = ""
        phone_match = re.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", text)
        if phone_match:
            phone = phone_match.group()

        # Check for website link
        website = ""
        links = div.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if href.startswith("http") and "google" not in href and "maps" not in href:
                website = href
                break

        businesses.append({
            "name": name,
            "address": address,
            "phone": phone,
            "website": website,
            "rating": rating,
            "review_count": review_count,
            "snippet": text[:300],
        })


def _parse_organic_results(soup, businesses):
    """
    Extract business info from organic Google results.
    Companies often show up with their Google Business profile info
    in the organic results too.
    """
    for h3 in soup.find_all("h3"):
        parent_a = h3.find_parent("a")
        if not parent_a or not parent_a.get("href", "").startswith("http"):
            continue

        url = parent_a["href"]
        title = h3.get_text(strip=True)

        # Skip non-business results
        if any(skip in url.lower() for skip in [
            "yelp.com/search", "yellowpages.com/search", "angi.com/search",
            "thumbtack.com/search", "homeadvisor.com/rated",
            "google.com", "facebook.com", "wikipedia.org",
            "bbb.org/search", "bizbuysell", "bizquest",
        ]):
            continue

        # Get the surrounding text for rating/review info
        result_div = h3
        for _ in range(6):
            if result_div.parent:
                result_div = result_div.parent
        full_text = result_div.get_text(" ", strip=True)

        # Must look like a business (has rating or phone)
        rating_match = re.search(r"(\d\.\d)\s*\((\d[\d,]*)\)", full_text)
        phone_match = re.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", full_text)

        if not rating_match and not phone_match:
            continue

        rating = float(rating_match.group(1)) if rating_match else None
        review_count = int(rating_match.group(2).replace(",", "")) if rating_match else 0
        phone = phone_match.group() if phone_match else ""

        # Address extraction
        address = ""
        addr_match = re.search(
            r"(\d+\s+[A-Za-z\s]+(?:St|Ave|Blvd|Rd|Dr|Ln|Way|Ct|Pl|Pkwy|Hwy)\.?[^·]*)",
            full_text, re.IGNORECASE
        )
        if addr_match:
            address = addr_match.group(1).strip()[:100]

        businesses.append({
            "name": title,
            "address": address,
            "phone": phone,
            "website": url,
            "rating": rating,
            "review_count": review_count,
            "snippet": full_text[:300],
        })


# ---------------------------------------------------------------------------
# Distress signal detection
# ---------------------------------------------------------------------------

# Review keywords that suggest a business is struggling or changing hands
REVIEW_DISTRESS_KEYWORDS = [
    "closed", "out of business", "permanently closed",
    "new ownership", "new owner", "under new management",
    "went downhill", "gone downhill", "not the same",
    "terrible", "worst", "avoid", "scam", "rip off",
    "never came back", "no show", "didn't show up",
    "lost their license", "shut down",
]


def _detect_distress_signals(business):
    """
    Analyze a business for distress signals.
    Returns a list of signal strings.
    """
    signals = []

    # Low Google rating (under 3.5 stars)
    if business.get("rating") is not None and business["rating"] < 3.5:
        signals.append(f"low rating ({business['rating']} stars)")

    # Very few reviews — established businesses should have more
    if business.get("review_count") is not None and business["review_count"] < 10:
        signals.append(f"very few reviews ({business['review_count']})")

    # No website — legit businesses usually have one
    if not business.get("website"):
        signals.append("no website listed")

    # Check snippet for distress keywords
    snippet = (business.get("snippet") or "").lower()
    for keyword in REVIEW_DISTRESS_KEYWORDS:
        if keyword in snippet:
            signals.append(f'review mention: "{keyword}"')

    return signals


# ---------------------------------------------------------------------------
# Convert to listing format (matches scraper.py output)
# ---------------------------------------------------------------------------

def _business_to_listing(business, search_area, industry):
    """
    Convert a raw business dict into the standard listing format
    used by filters.py and output.py.
    """
    distress_signals = _detect_distress_signals(business)

    # Build location string from address or search area
    location = business.get("address") or search_area

    # Build description with business details
    desc_parts = []
    if business.get("rating") is not None:
        desc_parts.append(f"{business['rating']} stars ({business.get('review_count', 0)} reviews)")
    if business.get("phone"):
        desc_parts.append(f"Phone: {business['phone']}")
    if business.get("website"):
        desc_parts.append(f"Website: {business['website']}")
    if distress_signals:
        desc_parts.append(f"Distress signals: {', '.join(distress_signals)}")

    description = " | ".join(desc_parts)

    return {
        "company": business["name"],
        "url": business.get("website") or f"https://www.google.com/maps/search/{business['name'].replace(' ', '+')}",
        "description": description,
        "location": location,
        "asking_price": None,       # Not for sale — no asking price
        "revenue": None,
        "cash_flow": None,
        "employees": None,          # Can't get this from Maps
        "industry": industry,
        "source": "Google Maps",
        "distress_signals": distress_signals,
        "rating": business.get("rating"),
        "review_count": business.get("review_count"),
        "phone": business.get("phone"),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

SEARCH_INDUSTRIES = ["plumbing company", "electrical company"]


def scrape_maps():
    """
    Search Google for plumbing/electrical companies in each configured
    metro area. Extract business details and flag distress signals.

    Returns listings in the same format as scraper.scrape_all().
    """
    config = _load_config()
    search_areas = config.get("maps_search_areas", [])
    max_per_area = config.get("maps_max_results_per_area", 10)

    if not search_areas:
        print("No maps_search_areas in config.json — skipping Maps scraper.")
        return []

    all_listings = []

    print("Starting Maps scraper...")
    with sync_playwright() as p:
        browser, context, page = _launch_browser(p)

        total_searches = len(SEARCH_INDUSTRIES) * len(search_areas)
        search_num = 0

        for industry_query in SEARCH_INDUSTRIES:
            # Determine industry label
            if "plumbing" in industry_query.lower():
                industry = "Plumbing"
            else:
                industry = "Electrical"

            for area in search_areas:
                search_num += 1
                query = f"{industry_query} near {area}"
                print(f"\n  Maps search {search_num}/{total_searches}: {query}")

                _polite_delay(3, 6)
                businesses = _google_search_maps(page, query, max_results=max_per_area)
                print(f"    Found {len(businesses)} businesses")

                for biz in businesses:
                    listing = _business_to_listing(biz, area, industry)
                    all_listings.append(listing)

        browser.close()

    # Deduplicate by company name (case-insensitive)
    seen_names = set()
    unique = []
    for listing in all_listings:
        key = listing["company"].lower().strip()
        if key and key not in seen_names:
            seen_names.add(key)
            unique.append(listing)

    print(f"\nMaps scraper: {len(unique)} unique businesses found")

    # Summary of distress signals
    distressed = [l for l in unique if l.get("distress_signals")]
    if distressed:
        print(f"  {len(distressed)} showing distress signals")

    return unique
