# Proposal — Lima Importadores Dashboard

**Change**: `lima-importadores-dashboard`
**Date**: 2026-05-06
**Status**: Proposed
**Phase**: propose

---

## 1. Intent

Build a market-research web dashboard that identifies import businesses in Lima, Peru that have a weak or non-existent web presence so they become high-conviction prospects for a "sell them a professional website" outreach.

The tool will:
- Scrape Google Maps for businesses in the import sector across Lima districts
- Persist raw + enriched data in a portable SQLite store
- Enrich each business with a website-quality signal (no site / outdated site)
- Apply a multi-criteria filter (sector, antigüedad, reviews, rating, web presence)
- Surface qualifying prospects through a filterable Streamlit dashboard with CSV/Excel export

**Why now**: The user is doing manual prospecting today. A semi-automated pipeline turns hours of clicking into minutes of filtering and produces a defensible, exportable lead list per district.

**Definition of success (v1)**:
- A single command runs the full pipeline (scrape → enrich → filter)
- The dashboard loads the SQLite file locally and lets the user filter by district + criteria
- The user can export the filtered list to CSV and Excel
- At least one full Lima district is scraped end-to-end without manual intervention

---

## 2. Scope

### In scope (v1)
- Playwright-based async scraper for Google Maps search results in the import vertical
- SQLite persistence (single `.db` file) via SQLAlchemy
- Website enrichment: HTTP fetch + BeautifulSoup footer parsing + Wayback CDX fallback for ambiguous cases
- Antigüedad heuristic based on the oldest review visible in the first batch + zero-review fallback
- Streamlit dashboard with district filter, criteria toggles, and CSV/Excel export
- Configurable district list (43 Lima districts + Callao)
- One-time scraping run (manual trigger)

### Out of scope (v1)
- Scheduling / cron / continuous re-scraping
- SUNAT RUC cross-reference (discarded in exploration — names rarely match razón social)
- Google Places API (cost + ToS concerns; Playwright scraping chosen)
- Proxy rotation (deferred — start without; add only if detection rates spike)
- Multi-user auth or hosted deployment (local Streamlit only)
- CRM integration / outbound email automation
- Other Peruvian cities or non-import verticals
- Mobile UI (desktop Streamlit only)
- Historical change tracking (snapshots over time)

---

## 3. Ideal Prospect Criteria (formal)

A business qualifies as an **ideal prospect** when ALL of the following hold:

| # | Criterion | Rule |
|---|-----------|------|
| 1 | **Sector** | Business category in Google Maps maps to "import" vertical (configurable keyword/category list) |
| 2 | **Location** | Address parses to one of the configured Lima districts (or Callao) |
| 3 | **Antigüedad** | At least one review visible in the first batch is dated ≥ 5 years ago **OR** the business has zero reviews. Otherwise flagged as `antigüedad: no determinada` (does not auto-qualify; surfaces for manual review) |
| 4 | **Low reviews** | `review_count < 50` |
| 5 | **Rating** | `rating ≥ 3.5` (or null when zero reviews — treated as pass) |
| 6 | **Weak web presence** | No `website` field in Maps profile **OR** website footer copyright year is older than 3 years **OR** Wayback CDX shows no captures in the last 2 years |

A business that fails any one of these is excluded from the prospect list but remains in the database for auditing.

---

## 4. Architecture

```
+-------------------+      +----------+      +--------------------+      +-------------------+
|  Playwright       |      |          |      |  Enrichment        |      |  Streamlit        |
|  Async Scraper    +----->+  SQLite  +----->+  (requests + BS4 + +----->+  Dashboard        |
|  (+ stealth)      |      |  (.db)   |      |   Wayback CDX)     |      |  (filter + export)|
+-------------------+      +----------+      +--------------------+      +-------------------+
```

### Components and responsibilities

- **Scraper (`scraper/`)**
  - Async Playwright with `playwright-stealth`
  - Iterates configured search queries × district seeds
  - Extracts: name, address, district (parsed), phone, website URL, review count, rating, category, place ID, GPS coords, oldest visible review date, opening hours
  - Writes raw rows to SQLite `businesses` table
  - Polite rate limiting; retries with backoff on transient failures

- **Storage (`storage/`)**
  - SQLite file (single artifact, portable)
  - SQLAlchemy models: `Business`, `Review` (oldest review only for v1), `WebsiteCheck`
  - Idempotent upserts keyed by `place_id`

- **Enrichment (`enrichment/`)**
  - For each business with a `website` URL:
    - HTTP GET (timeout, no JS render)
    - BeautifulSoup parse → look for copyright year in footer (regex: `©\s*(\d{4})`, plus common variants)
    - If ambiguous (no footer year, or year ≥ current − 3): query Wayback CDX API for last capture date
  - Writes a `WebsiteCheck` row with verdict: `no_site | outdated | current | unknown`

- **Filter / qualifier (`qualifier/`)**
  - Pure function over DB rows — applies the criteria in §3
  - Outputs a `prospects` view (or computed in-memory by the dashboard)

- **Dashboard (`dashboard/app.py`)**
  - Streamlit UI
  - Sidebar: district multiselect, criteria toggles, search box
  - Main: paginated table of qualifying prospects with key columns
  - Buttons: Export CSV, Export Excel (`pandas.to_excel`)

### Pipeline orchestration

A single CLI entrypoint (`python -m lima_importadores.run`) executes scrape → enrich → qualify in order. Each step is also runnable in isolation for debugging.

---

## 5. Key Decisions (already made)

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Scraping technology | Playwright async + playwright-stealth | Real browser; tolerates Maps' SPA; stealth reduces detection. Places API was rejected (cost + ToS) |
| Language / stack | Python-only | Single language across scraper, enrichment, and UI; team familiarity |
| Storage | SQLite via SQLAlchemy | Zero ops, portable single file, fits single-user use case |
| UI | Streamlit | Fastest to build a filterable table with export; no frontend stack required |
| Antigüedad heuristic | Oldest visible review ≥ 5y OR zero reviews; otherwise `no determinada` | SUNAT RUC matching was discarded — business names in Maps rarely match razón social. Reviews are the only reliable in-Maps signal |
| Website-age detection | Footer copyright year (BS4) + Wayback CDX fallback | Cheap, deterministic, no JS rendering needed for v1 |
| Districts | All 43 Lima districts + Callao, configurable | User can run subsets; full coverage by default |
| Proxies | None initially | Add only if blocks become a problem — start lean |
| Scheduling | Manual one-shot run | Out of scope for v1; add later if data drifts faster than re-runs |

---

## 6. Open Questions (must resolve before spec)

1. **Import sector definition** — what exact Google Maps categories / search keywords define "import sector" for Lima? (e.g. "importadora", "importaciones", specific category strings). Need a finalized seed list.
2. **Outdated website threshold** — confirm "older than 3 years" for footer copyright is the right cutoff, or should it be 2 years to be stricter?
3. **Wayback fallback policy** — when footer year is missing, do we fall back to Wayback for every such site, or only when the site responded but had no parseable footer? (Latency / API courtesy concern.)
4. **Phone normalization** — should we normalize Peruvian phone numbers (E.164) at scrape time or at export?
5. **Duplicate handling** — if the same `place_id` appears across multiple district searches, do we keep one row (upsert) or track which queries surfaced it?
6. **Rate limiting numbers** — concrete values for delays between Maps actions? (Suggest: 2-5s between scrolls, 30-60s between districts. Confirm in spec.)
7. **Excel export shape** — single sheet of prospects, or one sheet per district?

These are the questions sdd-spec needs answered (or assumed-with-a-default) before producing the spec.

---

## 7. Rollback Plan

This is a greenfield, isolated tool — rollback is low-risk:

- **Code**: lives in its own repo / folder (`lima_importadores/`). Abandoning means deleting the folder. No external systems mutated.
- **Data**: a single SQLite file. Delete `.db` to wipe state.
- **External effects**: none. The scraper only reads from Google Maps and target websites. No writes to third-party services. No accounts created. No API keys provisioned.
- **Cost recovery**: zero — no paid APIs are used in v1.
- **Partial rollback**: if only the dashboard underdelivers, the SQLite file + scraper remain valuable and can be queried directly with any SQLite client until a replacement UI is chosen.

If the project is abandoned mid-build, the only artifact to clean up is the working folder + `.db` file. No production migrations, no external state, no users to notify.

---

## 8. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Google IP blocks during scraping | High | Pipeline halts | Conservative rate limits; randomized delays; playwright-stealth; ability to plug in proxies later without architectural change |
| Google Maps DOM changes break selectors | Medium | Scraper produces empty / wrong rows | Centralize selectors in one module; add a smoke test that runs against a known place; expect 2-4 selector updates/year |
| Website age detection false positives (sites without copyright in footer, or outdated copyright on otherwise current site) | Medium | Some prospects mis-flagged | Two-signal approach (footer + Wayback); expose `unknown` verdict in dashboard so user can review manually |
| Google ToS violation | Low-Medium | Civil exposure only (no criminal in Peru); potential C&D | Personal/internal use, no resale of raw Maps data, low request volume, no circumvention of paid auth. Document use case |
| `antigüedad: no determinada` flag pollutes prospect list | Medium | Noise in output | Default dashboard view excludes `no determinada`; provide a toggle to include them for manual triage |
| Wayback CDX rate limits / downtime | Low | Some sites get `unknown` verdict | Cache results per domain; degrade gracefully to `unknown` |
| SQLite contention if dashboard runs while scraper writes | Low | Locked DB errors | Run scraper and dashboard in separate phases; use WAL mode |

---

## 9. Next Phase

Proceed to `sdd-spec` to produce a formal specification covering:
- Data model (tables, columns, indexes)
- Scraper contract (inputs, outputs, error modes)
- Enrichment contract (HTTP behavior, parsing rules, Wayback policy)
- Qualifier rules (exact predicate definitions matching §3)
- Dashboard requirements (filters, columns, export formats)
- Configuration surface (districts, keywords, thresholds)

`sdd-design` can run in parallel to detail module boundaries, async patterns, and selector strategy.
