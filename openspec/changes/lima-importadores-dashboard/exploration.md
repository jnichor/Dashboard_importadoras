# Exploration: lima-importadores-dashboard

**Status**: done
**Date**: 2026-05-06

## Executive Summary

This is a greenfield project to build an internal market research tool for identifying import businesses in Lima, Peru that lack a proper web presence. The recommended stack is Python-only: Playwright + playwright-stealth for scraping Google Maps, SQLite (via SQLAlchemy) for storage, and Streamlit for the dashboard. The tool can deliver a working first version in 3-5 days. The critical caveat is that Google Maps does NOT expose business founding year — the "5+ years in operation" filter criterion must be redesigned using review-date proxies or a SUNAT RUC cross-reference.

## Current State

Greenfield project. No existing code. Working directory contains only `.atl/skill-registry.md`.

## Tech Stack Options

**Option A — Python monolith with Streamlit** (RECOMMENDED)
Playwright + playwright-stealth + SQLite + Streamlit. Single language, fastest to build, no infrastructure.

**Option B — Python backend + Vue/Vanilla JS**
Playwright + SQLite + FastAPI + Vue. More UI flexibility, but much more setup.

**Option C — Python backend + Dash (Plotly)**
Playwright + SQLite + Plotly Dash. Middle ground — good interactivity, Python-only, more work than Streamlit.

## Scraping Approach

Google Maps is a JavaScript SPA — `requests` + `BeautifulSoup` alone is NOT usable.

| Tool | Stealth | Verdict |
|------|---------|---------|
| Playwright + playwright-stealth | Medium | **Recommended** |
| Playwright + Camoufox | High | Fallback (maintenance paused 2026) |
| Selenium + undetected-chromedriver | Medium | Viable but slower |
| Scrapy | None | Not usable (no JS rendering) |

**Scraping flow per district**:
1. Search: `"importador" OR "importaciones" {district} Lima`
2. Scroll results panel to load all listings (~20 per scroll, up to ~120 per search)
3. Click each listing → extract structured data
4. Move to next with random 2-8s delay

## Extractable Data Fields

| Field | Extractable | Notes |
|-------|-------------|-------|
| Business name | Yes | Always present |
| Address (full) | Yes | Parse district from address |
| Phone number | Yes | When listed |
| Website URL | Yes | Presence/absence is a direct filter criterion |
| Review count | Yes | Always present |
| Average rating | Yes | Always present |
| Business category | Yes | e.g., "Import/export company" |
| GPS coordinates | Yes | From URL or data-attributes |
| Place ID | Yes | Google's stable identifier |
| Opening hours | Yes | When listed |
| **Years in business** | **NO** | Not available as a structured field |

## "Years in Business" Problem

Google Maps does NOT expose founding year. Alternatives:
- **(a) Skip this filter** — simplest
- **(b) Oldest review date proxy** — if the oldest review is 5+ years ago, business has been active at least that long (requires scraping review dates — slow)
- **(c) SUNAT RUC cross-reference** — Peru's tax authority has public business registration dates; requires a separate lookup step

## "Outdated Website" Detection

For businesses with a website URL, detect if it's outdated:

| Method | Reliability | Cost |
|--------|-------------|------|
| HTTP `Last-Modified` header | Low | Free |
| Copyright year in footer HTML | Medium | Free (requests + BS4) |
| Wayback Machine CDX API | High | Free (slow) |
| BuiltWith / Wappalyzer API | High | Paid ($250+/mo) |

**Recommended**: `requests` + `BeautifulSoup` → parse copyright year from footer. Augment with Wayback Machine CDX API for uncertain cases.

## Storage

**SQLite via SQLAlchemy** — sufficient for Lima's import business dataset (estimated 500-3000 records total). Single portable file, zero infrastructure. Easy migration to PostgreSQL later.

**Schema sketch**:
```
businesses: id, place_id, name, address, district, phone, website_url,
            rating, review_count, category, has_website, website_outdated,
            website_copyright_year, scraped_at
scrape_runs: id, started_at, completed_at, query, district, results_count
```

## Architecture

```
[Scraper Layer]
    Playwright (async) + playwright-stealth
    Input: list of Lima districts × search keywords
    Output: raw business data → SQLite

[Enrichment Layer] (second pass)
    requests + BeautifulSoup on website URLs
    Wayback Machine CDX API for age estimation
    Output: website_outdated flag + copyright_year → SQLite

[Dashboard Layer]
    Streamlit app
    Reads from SQLite via SQLAlchemy + pandas
    Filters: district, min rating, max reviews, has_website (Y/N/outdated)
    Views: table + charts
    Export: CSV / Excel (st.download_button)
```

## Recommended Approach

**Playwright (async) + playwright-stealth + SQLite (SQLAlchemy) + Streamlit**

- Python-only stack → single developer, fast iteration
- SQLite is more than sufficient for this dataset size
- Streamlit covers all dashboard requirements including export
- Estimated time to first working version: 3-5 days

## Open Questions

1. **"Years in business"**: Skip filter, use oldest-review-date proxy, or SUNAT RUC cross-reference?
2. **Districts scope**: All 43 Lima districts initially, or a priority subset (Miraflores, San Isidro, La Victoria, Breña)?
3. **Proxy budget**: Residential proxy ($5-15/mo) to avoid IP blocks, or try without first?
4. **Data freshness**: One-time scrape or recurring refresh? (determines if scheduling is needed)
5. **Dashboard audience**: Personal use only, or shared with a sales team? (determines hosting model)

## Risks

| Risk | Severity | Notes |
|------|----------|-------|
| Google IP blocks mid-scrape | High | Aggressive rate limiting without proxies |
| Google Maps DOM changes break selectors | Medium | Expected 2-4x/year |
| "Years in business" field unavailable | Medium | Core criterion needs redesign |
| Website age detection unreliable | Medium | False positives/negatives from footer parsing |
| Google ToS violation | Low-Medium | Civil/ToS consequences only; no criminal exposure in Peru |
| playwright-stealth / Camoufox lag behind Chromium | Low | Monitor updates |
