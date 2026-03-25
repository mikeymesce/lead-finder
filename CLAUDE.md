# CLAUDE.md — DealFlow

> Read this every session.

## What This Is

Daily tool that finds small plumbing/electrical companies for sale in the tri-state area. Scores leads on deal quality + distress, deduplicates across runs, emails top 3. Built for Mike to source acquisition targets.

## Owner

- **Mike** — Not an engineer. Explain simply. Push back on bad ideas. Keep it working.

## Quick Reference

- **Run:** `python3 main.py` (add `--no-email` to skip email)
- **Config:** `config.json` (search criteria, scoring weights, email settings)
- **Output:** Google Sheet (primary) or `leads.csv` (fallback)
- **Entry point:** `main.py`
- **Key files:** `scraper.py`, `maps_scraper.py`, `filters.py`, `output.py`, `email_digest.py`
- **State files:** `seen_leads.json`, `skip_list.json`, `last_email.json`

## Rules

- Test before pushing. Always.
- Don't break the scraper silently — if a source changes its HTML, log an error, don't just return empty results.
- Keep it simple. One script should be runnable with one command.
- Update docs when files change.

## Documentation

| Doc | Purpose | Update when... |
|---|---|---|
| `docs/architecture.md` | File map, how it works | Files added/removed |
| `docs/vision.md` | Product roadmap | Direction changes |
| `docs/data-sources.md` | Which sites we scrape | Sources added/removed |
| `docs/google-sheets-setup.md` | Sheet setup instructions | Auth flow changes |
| `CHANGELOG.md` | What shipped | Every session |
| `README.md` | Overview + setup | Major changes |
