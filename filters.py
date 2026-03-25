"""
Filters and scores listings based on config criteria.
"""

import json


def load_config():
    """Load search criteria from config.json."""
    with open("config.json", "r") as f:
        return json.load(f)


def passes_filters(listing, config):
    """Check if a listing passes the hard filters (employees, location, industry)."""

    # Must be a relevant industry
    industry = (listing.get("industry") or "").lower()
    if industry and industry not in ["plumbing", "electrical", "electric", "unknown"]:
        return False

    # Employee count filter (if available)
    emp = listing.get("employees")
    if emp is not None:
        if emp < config["employees"]["min"] or emp > config["employees"]["max"]:
            return False

    # Cash flow / SDE filter (if available)
    cf = listing.get("cash_flow")
    if cf is not None:
        if cf < config["sde"]["min"] or cf > config["sde"]["max"]:
            return False

    # Location filter — check if any state name or code appears
    location = (listing.get("location") or "").lower()
    description = (listing.get("description") or "").lower()
    company = (listing.get("company") or "").lower()
    url = (listing.get("url") or "").lower()
    combined = f"{location} {description} {company} {url}"

    states = [s.lower() for s in config["states"]]
    codes = [c.lower() for c in config["state_codes"]]

    # If location info exists, verify it matches
    if location:
        if not any(s in combined for s in states + codes):
            return False

    return True


def score_listing(listing, config):
    """
    Score a listing 0-100. Higher = better match / more likely distressed.

    Scoring:
    - Distress keywords in description: +10 each (max 50)
    - Has employee count in range: +15
    - Has cash flow / SDE data: +15
    - Has asking price: +10
    - Has location data: +10
    """
    score = 0
    description = (listing.get("description") or "").lower()
    company = (listing.get("company") or "").lower()
    combined = f"{description} {company}"

    # Distress keywords — the main signal
    # Preserve any pre-existing distress signals (e.g., from Maps scraper)
    distress_found = list(listing.get("distress_signals") or [])
    for keyword in config["distress_keywords"]:
        if keyword.lower() in combined:
            distress_found.append(keyword)
            score += 10

    # Also score pre-existing distress signals (from Maps: low rating, no website, etc.)
    existing_count = len(listing.get("distress_signals") or [])
    score += existing_count * 8  # 8 points per Maps distress signal

    score = min(score, 50)  # Cap distress score at 50
    listing["distress_signals"] = distress_found

    # Data completeness bonuses
    emp = listing.get("employees")
    if emp is not None and config["employees"]["min"] <= emp <= config["employees"]["max"]:
        score += 15

    if listing.get("cash_flow") is not None:
        score += 15

    if listing.get("asking_price") is not None:
        score += 10

    if listing.get("location"):
        score += 10

    listing["score"] = score
    return score


def filter_and_rank(listings, config):
    """Filter listings, score them, return top N sorted by score."""

    # Apply hard filters
    passed = [l for l in listings if passes_filters(l, config)]
    print(f"Listings passing filters: {len(passed)} / {len(listings)}")

    # Score each listing
    for listing in passed:
        score_listing(listing, config)

    # Sort by score (highest first)
    passed.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Return top N
    max_results = config.get("max_results_per_day", 2)
    top = passed[:max_results]

    if top:
        print(f"\nTop {len(top)} leads:")
        for i, l in enumerate(top, 1):
            signals = ", ".join(l.get("distress_signals", [])) or "none detected"
            print(f"  {i}. {l['company']} (score: {l['score']}, distress: {signals})")
    else:
        print("\nNo listings matched your criteria today.")

    return top
