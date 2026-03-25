# CLAUDE.md — Lead Finder

> Read this every session.

## What This Is

Daily scraper that finds small plumbing/electrical companies for sale in the tri-state area. Built for Mike to source acquisition targets.

## Owner

- **Mike** — Not an engineer. Explain simply. Push back on bad ideas. Keep it working.

## Quick Reference

- **Run:** `python3 main.py`
- **Config:** `config.json` (search criteria)
- **Output:** Google Sheet (primary) or `leads.csv` (fallback)
- **Entry point:** `main.py`

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
