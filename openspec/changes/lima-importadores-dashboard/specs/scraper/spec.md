# Spec — Scraper

**Domain**: scraper
**Change**: lima-importadores-dashboard
**Date**: 2026-05-06

---

## Input

- `districts`: list of district names (strings) — from configuration
- `keywords`: list of search terms — default: `["importadora", "importaciones", "import"]`

## Search Query Construction

For each `(district, keyword)` pair, the scraper MUST construct a Google Maps search query:

```
{keyword} {district} Lima
```

Example: `importadora Miraflores Lima`

The scraper MUST iterate all `districts × keywords` combinations sequentially (not concurrently).

---

## Browser Setup

- The scraper MUST use Playwright in async mode (`async_playwright`).
- The scraper MUST apply `playwright-stealth` to the browser context before any navigation.
- The scraper MUST launch Chromium in headless mode.
- The scraper MUST set a realistic `User-Agent` header.
- The scraper MUST disable the `webdriver` navigator property.
- The browser context MUST NOT store cookies between district runs.

---

## Search and Pagination

1. Navigate to `https://www.google.com/maps/search/{encoded_query}`
2. Wait for the results panel to appear (selector: results list container).
3. Scroll the results panel to load more listings. Each scroll MUST be followed by a wait of **2–5 seconds** (random within range).
4. Repeat scrolling until no new listings appear after two consecutive scrolls, OR until 120 listings are loaded (whichever comes first).
5. Collect all visible listing elements.

The scraper MUST NOT click the "More results" button if it appears — scroll-based pagination is the only mechanism.

---

## Per-Listing Extraction

For each listing in the results panel, the scraper MUST click to open the detail panel and extract:

| Field | Source | Notes |
|-------|--------|-------|
| `name` | Detail panel — business name heading | Required |
| `address` | Detail panel — address line | May be absent |
| `phone` | Detail panel — phone line | As-is, no normalization |
| `website_url` | Detail panel — website button href | null if button absent |
| `rating` | Detail panel — star rating value | null if no reviews |
| `review_count` | Detail panel — review count text | Parse integer from "X reseñas" |
| `category` | Detail panel — category label | First category listed |
| `opening_hours` | Detail panel — hours summary | As-is string |
| `latitude` | URL or data attribute | Parse from Maps URL |
| `longitude` | URL or data attribute | Parse from Maps URL |
| `place_id` | URL or data attribute | Parse `!1s{place_id}` from URL |
| `oldest_review_date` | Reviews section — visible review timestamps | See §Oldest Review Date |

After extraction the scraper MUST close/dismiss the detail panel before moving to the next listing.

---

## Oldest Review Date Extraction

1. In the detail panel, locate the reviews section.
2. Read all visible review timestamps **without scrolling the reviews section** (first batch only).
3. Parse each timestamp to an absolute date. Google Maps shows:
   - Relative: "hace 6 años" → subtract from scrape date
   - Absolute: "mayo de 2018" → parse month + year
4. The scraper MUST record the **oldest** date found in the first batch as `oldest_review_date`.
5. If the reviews section is absent or no timestamps are parseable, `oldest_review_date` MUST be set to `null`.

The scraper MUST NOT scroll or paginate reviews — first visible batch only.

---

## District Parsing

The scraper MUST attempt to parse the district from the extracted `address` field using a configurable district name list. If a match is found, set `district` to the matched name. If no match, set `district` to the search seed district used for that query.

---

## Rate Limiting

| Trigger | Delay |
|---------|-------|
| Between scroll actions in results panel | 2–5 seconds (random) |
| Between clicking consecutive listings | 1–3 seconds (random) |
| Between districts | 30–60 seconds (random) |
| After a network error / retry | Exponential backoff starting at 5s, max 60s |

All delays MUST use `asyncio.sleep` with a random value within the specified range.

---

## Error Handling

- If a listing fails to extract after 2 retries, the scraper MUST skip it, log the error, and increment the `errors` counter in `scrape_runs`.
- If navigation to the search page fails after 3 retries, the scraper MUST skip the entire `(district, keyword)` pair and log the failure.
- If Google Maps returns a CAPTCHA or bot-detection page (detected by checking for known CAPTCHA selectors), the scraper MUST pause for 120 seconds before retrying once. If the second attempt also hits CAPTCHA, the scraper MUST stop and log a `BLOCKED` error.
- All errors MUST be written to a structured log file (`scraper.log`) with timestamp, district, keyword, and error message.

---

## Output Contract

For each successfully extracted listing, the scraper MUST write one row to the `businesses` table via an upsert on `place_id`. The `scrape_runs` table MUST be updated with `businesses_found` and `errors` counts when the run completes.

---

## Scenarios

**Given** a search for `"importadora Miraflores Lima"` returns 45 listings,
**When** the scraper processes all results,
**Then** 45 rows MUST be upserted into `businesses` with `district = 'Miraflores'`.

**Given** the same `place_id` appears in results for both `Miraflores` and `San Isidro` searches,
**When** both are processed,
**Then** exactly one row SHALL exist in `businesses` for that `place_id`, updated with the most recent `scraped_at`.

**Given** Google Maps returns a CAPTCHA page during a district search,
**When** the scraper detects it,
**Then** the scraper MUST wait 120 seconds, retry once, and if still blocked, stop and log `BLOCKED`.

**Given** a listing detail panel does not contain a website button,
**When** the scraper extracts the listing,
**Then** `website_url` MUST be `null` and `has_website` MUST be `0`.

**Given** the reviews section shows timestamps "hace 7 años" and "hace 2 años",
**When** the scraper parses them,
**Then** `oldest_review_date` MUST be set to the date 7 years before the scrape date.
