#!/usr/bin/env python3
"""
Lead Finder — Daily acquisition target scraper.

Searches business-for-sale marketplaces for small plumbing/electrical
companies in the tri-state area. Prioritizes distressed sales.

Usage:
    python3 main.py
"""

import os
import sys
from datetime import datetime

# Make sure we're running from the project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from scraper import scrape_all
from filters import load_config, filter_and_rank
from output import save_leads


def main():
    print(f"{'='*50}")
    print(f"Lead Finder — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # Load search criteria
    config = load_config()
    print(f"Searching for: {', '.join(config['industries'])}")
    print(f"Location: {', '.join(config['states'])}")
    print(f"Employees: {config['employees']['min']}-{config['employees']['max']}")
    print(f"SDE range: ${config['sde']['min']:,}-${config['sde']['max']:,}")
    print()

    # Scrape all sources
    raw_listings = scrape_all()

    if not raw_listings:
        print("\nNo listings found from any source. Sites may be blocking or down.")
        print("Check the errors above for details.")
        sys.exit(1)

    # Filter and rank
    top_leads = filter_and_rank(raw_listings, config)

    # Save results
    save_leads(top_leads)

    print(f"\n{'='*50}")
    print("Done!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
