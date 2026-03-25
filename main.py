#!/usr/bin/env python3
"""
DealFlow — Daily acquisition target finder.

Searches business-for-sale marketplaces AND Google Maps for small
plumbing/electrical companies in the tri-state area. Scores leads
on deal quality + distress signals, emails top 3 every few days.

Usage:
    python3 main.py                    # Run both scrapers + email
    python3 main.py --marketplace-only # Only marketplace listings
    python3 main.py --maps-only        # Only Google Maps businesses
    python3 main.py --no-email         # Skip email digest
"""

import os
import sys
from datetime import datetime

# Make sure we're running from the project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from scraper import scrape_all
from maps_scraper import scrape_maps
from filters import load_config, filter_and_rank
from output import save_leads
from email_digest import send_email


def main():
    # Parse command-line flags
    marketplace_only = "--marketplace-only" in sys.argv
    maps_only = "--maps-only" in sys.argv
    no_email = "--no-email" in sys.argv

    if marketplace_only and maps_only:
        print("ERROR: Can't use both --marketplace-only and --maps-only. Pick one.")
        sys.exit(1)

    print(f"{'='*50}")
    print(f"DealFlow — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # Load search criteria
    config = load_config()
    print(f"Searching for: {', '.join(config['industries'])}")
    print(f"Location: {', '.join(config['states'])}")
    print(f"Employees: {config['employees']['min']}-{config['employees']['max']}")
    print(f"SDE range: ${config['sde']['min']:,}-${config['sde']['max']:,}")
    print(f"Asking price max: ${config['asking_price']['max']:,}")

    if maps_only:
        print(f"Mode: Google Maps only")
    elif marketplace_only:
        print(f"Mode: Marketplace only")
    else:
        print(f"Mode: All sources")
    print()

    raw_listings = []

    # --- Phase 1: Marketplace scraper (BizBuySell, etc.) ---
    if not maps_only:
        print("--- Marketplace Scraper ---")
        marketplace_results = scrape_all()
        raw_listings.extend(marketplace_results)
        print(f"Marketplace: {len(marketplace_results)} listings\n")

    # --- Phase 2: Google Maps scraper ---
    if not marketplace_only:
        print("--- Google Maps Scraper ---")
        maps_results = scrape_maps()
        raw_listings.extend(maps_results)
        print(f"Maps: {len(maps_results)} businesses\n")

    if not raw_listings:
        print("\nNo listings found from any source. Sites may be blocking or down.")
        print("Check the errors above for details.")
        sys.exit(1)

    print(f"\nTotal raw results: {len(raw_listings)}")

    # Filter and rank
    top_leads = filter_and_rank(raw_listings, config)

    # Save results (handles dedup, skip list, CSV, Sheets)
    saved_leads = save_leads(top_leads)

    # --- Email digest ---
    if no_email:
        print("\nEmail: skipped (--no-email flag)")
    elif saved_leads:
        sent, message = send_email(saved_leads, config)
        status = "SENT" if sent else "SKIPPED"
        print(f"\nEmail: {status} — {message}")
    else:
        print("\nEmail: skipped (no leads to send)")

    print(f"\n{'='*50}")
    print("Done!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
