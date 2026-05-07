# Spec — Qualifier

**Domain**: qualifier
**Change**: lima-importadores-dashboard
**Date**: 2026-05-06

---

## Purpose

The qualifier evaluates each business against the 6 prospect criteria and sets `prospect_qualifies` and `disqualify_reason` on the `businesses` row. It is a pure computation step — no scraping, no HTTP requests.

The qualifier MAY run as a post-processing step after enrichment, or MAY be computed on-the-fly in the dashboard. In either case, the logic MUST be identical.

---

## The 6 Criteria (ALL must pass to qualify)

### Criterion 1 — Sector

**Rule**: The business `category` or `name` MUST contain at least one of the configured import keywords (case-insensitive): `importadora`, `importaciones`, `import`.

- Match is case-insensitive substring search.
- If both `category` and `name` are null → **disqualify** (reason: `sector_unknown`).
- If neither field contains a keyword → **disqualify** (reason: `sector_no_match`).

### Criterion 2 — Location

**Rule**: The business `district` MUST be a non-null value present in the configured district list.

- If `district` is null → **disqualify** (reason: `district_unknown`).
- If `district` is not in the configured list → **disqualify** (reason: `district_out_of_scope`).

### Criterion 3 — Antigüedad

**Rule**:
- If `review_count = 0` → `antigüedad_flag = 'califica'` → **passes this criterion**.
- If `oldest_review_date` is not null AND `oldest_review_date <= today - 5 years` → `antigüedad_flag = 'califica'` → **passes**.
- Otherwise → `antigüedad_flag = 'no_determinada'` → **does not auto-qualify** (manual review flag, not a hard disqualify).

Businesses with `antigüedad_flag = 'no_determinada'` SHALL be stored in the database and surfaced in the dashboard with a visual indicator, but SHALL NOT appear in the default "qualifies" view.

### Criterion 4 — Low Reviews

**Rule**: `review_count < 50`.

- If `review_count >= 50` → **disqualify** (reason: `too_many_reviews`).
- If `review_count = 0` → **passes** (zero reviews is ideal).

### Criterion 5 — Rating

**Rule**: `rating >= 3.5` OR `rating IS NULL`.

- `rating IS NULL` occurs when `review_count = 0` — treated as **pass**.
- If `rating < 3.5` → **disqualify** (reason: `low_rating`).

### Criterion 6 — Weak Web Presence

**Rule**: At least one of the following MUST be true:
- `has_website = 0` (no website listed in Maps), OR
- The corresponding `website_checks` row has `verdict IN ('outdated', 'no_site')`.

If `website_checks.verdict = 'current'` → **disqualify** (reason: `website_current`).
If `website_checks.verdict = 'unknown'` → treat as **passes** (benefit of the doubt — surface for manual review with `unknown` badge in dashboard).
If no `website_checks` row exists yet (enrichment not run) → treat as **passes** for now; re-evaluate after enrichment.

---

## Output

For each business, the qualifier MUST set:

| Field | Value |
|-------|-------|
| `prospect_qualifies` | `1` if all 6 criteria pass, `0` if any hard-disqualify, `NULL` if blocked on `no_determinada` |
| `disqualify_reason` | Comma-separated reason codes if `prospect_qualifies = 0`, else `NULL` |
| `antigüedad_flag` | `'califica'` \| `'no_califica'` \| `'no_determinada'` |

---

## Scenarios

**Given** a business with `review_count = 0`, `rating = null`, `has_website = 0`, `category = "Importadora de electrodomésticos"`, `district = "La Victoria"`,
**When** the qualifier runs,
**Then** `prospect_qualifies = 1` and all criteria SHALL pass.

**Given** a business with `review_count = 75`,
**When** the qualifier runs,
**Then** `prospect_qualifies = 0` and `disqualify_reason` SHALL contain `too_many_reviews`.

**Given** a business with `review_count = 10`, all reviews within the last 3 years, `oldest_review_date` = 2 years ago,
**When** the qualifier runs,
**Then** `antigüedad_flag = 'no_determinada'` and `prospect_qualifies = NULL`.

**Given** a business with `website_checks.verdict = 'current'`,
**When** the qualifier runs,
**Then** `prospect_qualifies = 0` and `disqualify_reason` SHALL contain `website_current`.

**Given** a business with `website_checks.verdict = 'unknown'`,
**When** the qualifier runs,
**Then** criterion 6 SHALL pass and the business SHALL be evaluated on the remaining 5 criteria.
