"""
Filters and scores listings based on config criteria.

Scoring model:
  - Deal Quality (0-45): SDE range, price-to-SDE ratio
  - Distress (0-50+): keyword detection + Maps signals
  - Red Flags (negative): missing financials, legal issues
"""

import json
import re


def load_config():
    """Load search criteria from config.json."""
    with open("config.json", "r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Hard filters — pass/fail checks before scoring
# ---------------------------------------------------------------------------

def passes_filters(listing, config):
    """Check if a listing passes the hard filters (employees, location, industry)."""

    # Must be a relevant industry
    industry = (listing.get("industry") or "").lower()
    if industry and industry not in ["plumbing", "electrical", "electric", "plumbing/electrical", "unknown"]:
        return False

    # Employee count filter (if available) — max 40
    emp = listing.get("employees")
    if emp is not None:
        if emp < config["employees"]["min"] or emp > config["employees"]["max"]:
            return False

    # Asking price hard cap (if available)
    price = listing.get("asking_price")
    price_max = config.get("asking_price", {}).get("max")
    if price is not None and price_max is not None:
        if price > price_max:
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


# ---------------------------------------------------------------------------
# Scoring — Deal Quality
# ---------------------------------------------------------------------------

def _score_deal_quality(listing, config):
    """
    Score based on financial attractiveness.
    Returns (score, details_dict).
    """
    score = 0
    details = {}
    weights = config.get("scoring", {}).get("deal_quality", {})

    sde = listing.get("cash_flow")
    price = listing.get("asking_price")

    # SDE in target range ($100K-$1M)
    if sde is not None:
        sde_min = config["sde"]["min"]
        sde_max = config["sde"]["max"]
        if sde_min <= sde <= sde_max:
            pts = weights.get("sde_in_range", 25)
            score += pts
            details["sde_in_range"] = pts

    # Price-to-SDE ratio
    ratio = None
    if price is not None and sde is not None and sde > 0:
        ratio = round(price / sde, 2)
        listing["price_to_sde_ratio"] = ratio

        if ratio < 3:
            pts = weights.get("price_sde_ratio_under_3", 20)
            score += pts
            details["price_sde_ratio"] = f"{ratio}x (+{pts})"
        elif ratio <= 4:
            pts = weights.get("price_sde_ratio_3_to_4", 10)
            score += pts
            details["price_sde_ratio"] = f"{ratio}x (+{pts})"
        elif ratio > 5:
            pts = weights.get("price_sde_ratio_over_5", -10)
            score += pts
            details["price_sde_ratio"] = f"{ratio}x ({pts})"
    else:
        listing["price_to_sde_ratio"] = None

    return score, details


# ---------------------------------------------------------------------------
# Scoring — Distress Signals
# ---------------------------------------------------------------------------

# Keyword groups mapped to score values
DISTRESS_KEYWORD_GROUPS = [
    {
        "keywords": ["death", "estate", "probate", "deceased", "passed away"],
        "label": "death/estate/probate",
        "config_key": "death_estate_probate",
        "default": 25,
    },
    {
        "keywords": ["divorce", "divorcing"],
        "label": "divorce",
        "config_key": "divorce",
        "default": 20,
    },
    {
        "keywords": ["retiring", "retirement", "retired"],
        "label": "retiring",
        "config_key": "retiring",
        "default": 15,
    },
    {
        "keywords": ["health", "illness", "medical"],
        "label": "health/illness",
        "config_key": "health_illness",
        "default": 15,
    },
    {
        "keywords": ["must sell", "motivated seller", "price reduced", "reduced price", "priced to sell"],
        "label": "motivated/price reduced",
        "config_key": "must_sell_motivated_price_reduced",
        "default": 10,
    },
    {
        "keywords": ["relocating", "moving", "burnout", "burned out"],
        "label": "relocating/burnout",
        "config_key": "relocating_burnout",
        "default": 5,
    },
]


def _score_distress(listing, config):
    """
    Score based on distress signals in description and company name.
    Also preserves pre-existing distress signals from Maps scraper.
    Returns (score, signals_list).
    """
    score = 0
    signals = []
    weights = config.get("scoring", {}).get("distress", {})

    description = (listing.get("description") or "").lower()
    company = (listing.get("company") or "").lower()
    combined = f"{description} {company}"

    # Check each keyword group — only count each group once
    for group in DISTRESS_KEYWORD_GROUPS:
        for kw in group["keywords"]:
            if kw in combined:
                pts = weights.get(group["config_key"], group["default"])
                score += pts
                signals.append(group["label"])
                break  # Only count each group once

    # Preserve pre-existing distress signals from Maps scraper
    # (low rating, no website, few reviews, review mentions)
    existing_signals = listing.get("distress_signals") or []
    for sig in existing_signals:
        if sig not in signals:
            signals.append(sig)
            score += 8  # 8 points per Maps distress signal

    return score, signals


# ---------------------------------------------------------------------------
# Scoring — Red Flags (negative)
# ---------------------------------------------------------------------------

RED_FLAG_LEGAL_KEYWORDS = [
    "lawsuit", "lien", "litigation", "violation",
]


def _score_red_flags(listing, config):
    """
    Detect red flags that lower a listing's score.
    Returns (score, flags_list). Score will be 0 or negative.
    """
    score = 0
    flags = []
    weights = config.get("scoring", {}).get("red_flags", {})

    # No financials — no asking price AND no cash flow
    if listing.get("asking_price") is None and listing.get("cash_flow") is None:
        pts = weights.get("no_financials", -10)
        score += pts
        flags.append("no financials")

    # Legal red flags in description
    description = (listing.get("description") or "").lower()
    for kw in RED_FLAG_LEGAL_KEYWORDS:
        if kw in description:
            pts = weights.get("lawsuits_liens", -20)
            score += pts
            flags.append(f"legal: {kw}")
            break  # Only penalize once for legal issues

    return score, flags


# ---------------------------------------------------------------------------
# Combined scoring
# ---------------------------------------------------------------------------

def score_listing(listing, config):
    """
    Score a listing using the three-part model:
      Deal Quality + Distress - Red Flags = Total Score

    Stores breakdown on the listing dict for output.
    """
    deal_score, deal_details = _score_deal_quality(listing, config)
    distress_score, distress_signals = _score_distress(listing, config)
    red_flag_score, red_flags = _score_red_flags(listing, config)

    total = deal_score + distress_score + red_flag_score

    # Store everything on the listing for output
    listing["score"] = total
    listing["deal_quality_score"] = deal_score
    listing["distress_score"] = distress_score
    listing["red_flag_score"] = red_flag_score
    listing["distress_signals"] = distress_signals
    listing["red_flags"] = red_flags

    return total


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

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

    # Separate by source for quota enforcement
    marketplace = [l for l in passed if l.get("source") != "Google Maps"]
    maps = [l for l in passed if l.get("source") == "Google Maps"]

    max_marketplace = config.get("max_marketplace", 3)
    max_maps = config.get("max_maps", 3)

    top_marketplace = marketplace[:max_marketplace]
    top_maps = maps[:max_maps]

    # Combine and re-sort
    top = sorted(top_marketplace + top_maps, key=lambda x: x.get("score", 0), reverse=True)

    if top:
        print(f"\nTop {len(top)} leads:")
        for i, l in enumerate(top, 1):
            signals = ", ".join(l.get("distress_signals", [])) or "none detected"
            ratio = l.get("price_to_sde_ratio")
            ratio_str = f", P/SDE: {ratio}x" if ratio else ""
            print(f"  {i}. {l['company']} (score: {l['score']}, "
                  f"deal: {l.get('deal_quality_score', 0)}, "
                  f"distress: {l.get('distress_score', 0)}, "
                  f"flags: {l.get('red_flag_score', 0)}{ratio_str})")
            print(f"     Signals: {signals}")
    else:
        print("\nNo listings matched your criteria today.")

    return top
