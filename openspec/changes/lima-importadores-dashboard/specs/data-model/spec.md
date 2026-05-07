# Spec — Data Model

**Domain**: data-model
**Change**: lima-importadores-dashboard
**Date**: 2026-05-06

---

## Tables

### `businesses`

Primary store for every business scraped from Google Maps. One row per unique `place_id`.

| Column | Type | Nullable | Constraints | Notes |
|--------|------|----------|-------------|-------|
| `id` | INTEGER | No | PRIMARY KEY AUTOINCREMENT | Internal ID |
| `place_id` | TEXT | No | UNIQUE | Google Maps stable identifier |
| `name` | TEXT | No | | Business name as shown in Maps |
| `address` | TEXT | Yes | | Full address string |
| `district` | TEXT | Yes | | Parsed from address or inferred from search seed |
| `phone` | TEXT | Yes | | As-is from Maps — no normalization |
| `website_url` | TEXT | Yes | | URL as listed in Maps profile |
| `has_website` | INTEGER | No | DEFAULT 0 | 1 if website_url is not null |
| `rating` | REAL | Yes | CHECK rating >= 0 AND rating <= 5 | Average star rating |
| `review_count` | INTEGER | No | DEFAULT 0 CHECK >= 0 | Total number of reviews |
| `category` | TEXT | Yes | | Business category from Maps |
| `opening_hours` | TEXT | Yes | | Raw string from Maps |
| `latitude` | REAL | Yes | | GPS latitude |
| `longitude` | REAL | Yes | | GPS longitude |
| `oldest_review_date` | TEXT | Yes | ISO 8601 date | Oldest review date visible in first batch |
| `antigüedad_flag` | TEXT | No | DEFAULT 'no_determinada' | 'califica' \| 'no_califica' \| 'no_determinada' |
| `prospect_qualifies` | INTEGER | Yes | | 1 = qualifies, 0 = disqualifies, NULL = not yet evaluated |
| `disqualify_reason` | TEXT | Yes | | Human-readable reason if prospect_qualifies = 0 |
| `scraped_at` | TEXT | No | ISO 8601 datetime | When this row was last written |

**Upsert key**: `place_id` — if the same place_id appears in multiple district searches, the existing row MUST be updated (not duplicated).

**Indexes**:
- `idx_businesses_district` ON `businesses(district)`
- `idx_businesses_prospect` ON `businesses(prospect_qualifies)`
- `idx_businesses_scraped_at` ON `businesses(scraped_at)`

---

### `website_checks`

One row per business that has a `website_url`. Written by the enrichment step.

| Column | Type | Nullable | Constraints | Notes |
|--------|------|----------|-------------|-------|
| `id` | INTEGER | No | PRIMARY KEY AUTOINCREMENT | |
| `business_id` | INTEGER | No | FK → businesses.id | |
| `place_id` | TEXT | No | UNIQUE | Denormalized for fast lookup |
| `http_status` | INTEGER | Yes | | HTTP response code (null if unreachable) |
| `copyright_year` | INTEGER | Yes | | Parsed year from footer (null if not found) |
| `wayback_last_capture` | TEXT | Yes | ISO 8601 date | Last capture date from Wayback CDX (null if not queried) |
| `verdict` | TEXT | No | | 'no_site' \| 'outdated' \| 'current' \| 'unknown' |
| `checked_at` | TEXT | No | ISO 8601 datetime | |

**Verdict rules**:
- `no_site` — business has no website_url
- `outdated` — copyright_year < current_year - 5, OR wayback_last_capture < 2 years ago
- `current` — copyright_year >= current_year - 5 AND (wayback not queried OR wayback recent)
- `unknown` — site responded but no copyright year found AND Wayback CDX unavailable or returned no captures

**Indexes**:
- `idx_website_checks_place_id` ON `website_checks(place_id)`
- `idx_website_checks_verdict` ON `website_checks(verdict)`

---

### `scrape_runs`

Audit log of each scraping session.

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | INTEGER | No | PRIMARY KEY AUTOINCREMENT |
| `started_at` | TEXT | No | ISO 8601 datetime |
| `completed_at` | TEXT | Yes | NULL while running |
| `districts_queried` | TEXT | No | JSON array of district names |
| `keywords_used` | TEXT | No | JSON array of keywords |
| `businesses_found` | INTEGER | Yes | Total rows written/updated |
| `errors` | INTEGER | Yes | Count of skipped listings due to errors |

---

## Scenarios

**Given** a scraper run extracts two listings with the same place_id from different district searches,
**When** both are written to the database,
**Then** there SHALL be exactly one row in `businesses` with that place_id, with the `scraped_at` timestamp of the most recent upsert.

**Given** a business has no `website_url`,
**When** the enrichment step runs,
**Then** a `website_checks` row SHALL be written with `verdict = 'no_site'` and no HTTP fetch SHALL be attempted.

**Given** a business has `review_count = 0` and no `oldest_review_date`,
**When** the qualifier runs,
**Then** `antigüedad_flag` SHALL be set to `'califica'`.

**Given** a business has reviews but all visible review dates are within the last 5 years,
**When** the qualifier runs,
**Then** `antigüedad_flag` SHALL be set to `'no_determinada'` and the business SHALL NOT auto-qualify.
