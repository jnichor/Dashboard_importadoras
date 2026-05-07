# Spec — Enrichment

**Domain**: enrichment
**Change**: lima-importadores-dashboard
**Date**: 2026-05-06

---

## Purpose

The enrichment step runs after scraping. For each business that has a `website_url`, it determines whether the website is current or outdated and writes a verdict to `website_checks`.

---

## Input

All rows in `businesses` where `has_website = 1` and no `website_checks` row exists yet (i.e., not previously enriched). Enrichment is idempotent — re-running MUST skip already-checked businesses.

---

## HTTP Fetch

- The enrichment MUST use the `requests` library (synchronous, no Playwright).
- Each fetch MUST set a realistic `User-Agent` header (same as scraper).
- Timeout: **10 seconds** per request (connect + read combined).
- The enrichment MUST NOT follow more than 3 redirects.
- The enrichment MUST NOT render JavaScript — plain HTTP GET only.
- If the fetch raises any exception (timeout, connection error, SSL error), the business MUST receive verdict `unknown` and the error MUST be logged.

---

## Copyright Year Parsing

After a successful HTTP response (status 200), the enrichment MUST:

1. Parse the response body with BeautifulSoup.
2. Search for copyright year patterns in this priority order:
   - `<footer>` tag content
   - Elements with class names containing "footer", "copyright", "copy"
   - Full page body as fallback
3. Apply these regex patterns (in order, first match wins):

| Pattern | Example match |
|---------|--------------|
| `©\s*(\d{4})` | `© 2014` |
| `[Cc]opyright\s+(\d{4})` | `Copyright 2014` |
| `(\d{4})\s*©` | `2014 ©` |
| `(\d{4})\s+[Aa]ll [Rr]ights` | `2014 All rights reserved` |

4. If multiple years are found, use the **most recent** one (conservative — avoids false positives on "Est. 2010 © 2023" patterns).
5. If no year is found, proceed to the Wayback CDX fallback.

**Outdated threshold**: A copyright year is considered outdated if `copyright_year < current_year - 5`. As of 2026, this means copyright year ≤ 2020.

---

## Wayback CDX Fallback

The Wayback fallback MUST be triggered **only when**:
- The HTTP fetch succeeded (status 200), AND
- No copyright year was found in the page.

The fallback MUST NOT be triggered if the fetch failed (network error, timeout, non-200 status).

**CDX API call**:
```
GET https://web.archive.org/cdx/search/cdx
  ?url={website_url}
  &output=json
  &limit=1
  &fl=timestamp
  &from=20200101
  &filter=statuscode:200
  &fastLatest=true
```

- Timeout: **15 seconds**.
- If the CDX API is unreachable or returns an error, degrade gracefully to verdict `unknown`.
- Parse the `timestamp` field (format: `YYYYMMDDHHmmss`) to extract the last capture date.
- If last capture date < 2 years before today → verdict `outdated`.
- If last capture date >= 2 years before today → verdict `current`.
- If CDX returns an empty result (no captures) → verdict `outdated` (site has no recent internet presence).

---

## Verdict State Machine

```
website_url is null
    → verdict = 'no_site' (no fetch)

website_url present
    → HTTP fetch
        → fetch failed (timeout / error / non-200)
            → verdict = 'unknown'
        → fetch succeeded (200)
            → parse copyright year
                → year found AND year < current_year - 5
                    → verdict = 'outdated'
                → year found AND year >= current_year - 5
                    → verdict = 'current'
                → year NOT found
                    → Wayback CDX fallback
                        → CDX success: last capture < 2 years ago
                            → verdict = 'current'
                        → CDX success: last capture >= 2 years ago OR no captures
                            → verdict = 'outdated'
                        → CDX failed / unavailable
                            → verdict = 'unknown'
```

---

## Output Contract

For each processed business, the enrichment MUST write one row to `website_checks` with:
- `business_id`, `place_id`
- `http_status` (null if fetch not attempted)
- `copyright_year` (null if not found)
- `wayback_last_capture` (null if not queried)
- `verdict`
- `checked_at`

---

## Scenarios

**Given** a business has `website_url = null`,
**When** enrichment runs,
**Then** a `website_checks` row MUST be written with `verdict = 'no_site'` and no HTTP request SHALL be made.

**Given** a business website returns HTTP 200 with `© 2018` in the footer,
**When** enrichment runs in 2026,
**Then** `copyright_year = 2018`, `verdict = 'outdated'` (2018 < 2026 - 5 = 2021).

**Given** a business website returns HTTP 200 with `© 2023` in the footer,
**When** enrichment runs in 2026,
**Then** `copyright_year = 2023`, `verdict = 'current'` (2023 >= 2021).

**Given** a business website returns HTTP 200 but has no copyright year in the page,
**When** enrichment runs,
**Then** the Wayback CDX API MUST be queried for that URL.

**Given** a business website times out after 10 seconds,
**When** enrichment runs,
**Then** `verdict = 'unknown'` and NO Wayback CDX query SHALL be made.

**Given** the Wayback CDX API returns no captures for a URL,
**When** enrichment processes it as fallback,
**Then** `verdict = 'outdated'`.
