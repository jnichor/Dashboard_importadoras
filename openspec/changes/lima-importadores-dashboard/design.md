# Design — Lima Importadores Dashboard

**Change**: lima-importadores-dashboard
**Date**: 2026-05-06

---

## 1. Module Structure

```
lima_importadores/
├── __main__.py              # CLI entrypoint: run scrape → enrich → qualify
├── config.py                # Config loading + Pydantic model
├── scraper/
│   ├── __init__.py
│   ├── browser.py           # Playwright context setup + stealth
│   ├── maps.py              # Search, scroll, per-listing extraction
│   └── selectors.py         # ALL CSS/XPath selectors centralized here
├── storage/
│   ├── __init__.py
│   ├── models.py            # SQLAlchemy declarative models
│   └── repository.py        # Upsert + query methods (no raw SQL outside here)
├── enrichment/
│   ├── __init__.py
│   ├── fetcher.py           # HTTP GET with timeout/headers
│   ├── parser.py            # Copyright year regex extraction
│   └── wayback.py           # Wayback CDX API client
├── qualifier/
│   ├── __init__.py
│   └── rules.py             # Pure functions — no DB access
├── dashboard/
│   └── app.py               # Streamlit application
├── config.yaml              # User configuration (gitignored if contains secrets)
├── requirements.txt
└── data/
    └── .gitkeep             # SQLite file lives here (gitignored)
```

---

## 2. Async Architecture

### Playwright Event Loop

The scraper runs inside a single `asyncio.run()` call in `__main__.py`. The Playwright browser context is created once per run and reused across all districts × keywords.

```python
async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=REALISTIC_UA)
        await stealth_async(context)  # playwright-stealth
        for district in config.districts:
            for keyword in config.keywords:
                await scrape_query(context, district, keyword)
            await asyncio.sleep(random_delay(district_min, district_max))
        await browser.close()
```

### Sequential Districts, Sequential Keywords

Districts and keywords iterate **sequentially** — never concurrently. Rationale: concurrent Maps requests from the same IP dramatically increases detection probability. The performance loss is acceptable because the bottleneck is rate-limiting delays, not CPU.

### Enrichment Concurrency

Enrichment (HTTP fetches to business websites) runs **sequentially** via synchronous `requests`. These are different domains — no detection risk from concurrent requests — but keeping it sequential reduces complexity and memory footprint for v1. Concurrency can be added later with `httpx` + `asyncio.gather` if enrichment becomes a bottleneck.

### SQLAlchemy Session Management

The scraper uses a synchronous SQLAlchemy session (not async). Since scraping is sequential, there is no concurrent write pressure. The session is created once per run and committed after each district completes (not after each listing, to reduce write amplification).

WAL mode is enabled at database creation:
```python
engine = create_engine(db_path, connect_args={"check_same_thread": False})
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
```

This allows the Streamlit dashboard to read while a scraper session is open.

---

## 3. Selector Strategy

### Centralized in `selectors.py`

All Google Maps DOM selectors live in one file. No selector strings appear anywhere else in the codebase. This is the single most important maintenance decision — when Google changes the Maps UI, only `selectors.py` needs updating.

```python
# selectors.py
RESULTS_PANEL = '[role="feed"]'
LISTING_ITEM  = '[role="feed"] > div > div[jsaction]'
DETAIL_NAME   = 'h1.DUwDvf'
DETAIL_ADDRESS = '[data-item-id="address"] .Io6YTe'
DETAIL_PHONE   = '[data-item-id^="phone"] .Io6YTe'
DETAIL_WEBSITE = 'a[data-item-id="authority"]'
DETAIL_RATING  = 'div.F7nice span[aria-hidden="true"]'
DETAIL_REVIEWS = 'div.F7nice span[aria-label$="reseñas"]'
DETAIL_CATEGORY = 'button.DkEaL'
REVIEW_ITEMS   = 'div.jftiEf'
REVIEW_DATE    = 'span.rsqaWe'
```

**Prefer `data-*` attributes and `aria-*` attributes over class names.** Google Maps uses generated, unstable class names (e.g., `DUwDvf`). Data attributes and ARIA roles are more stable across DOM updates.

### Smoke Test

On startup, `browser.py` runs a smoke test against a known stable Place ID (hardcoded in config — a well-known Lima business with a stable Maps profile). If the smoke test fails to extract the business name, the scraper logs `SELECTOR_STALE` and exits before processing any data, preventing silent empty results.

---

## 4. Enrichment Pipeline

```
businesses (has_website=1, not yet checked)
    │
    ▼
fetcher.py → HTTP GET (10s timeout, no JS, 3 redirects max)
    │
    ├── fetch failed → verdict='unknown', log error, next business
    │
    └── fetch ok (200)
            │
            ▼
        parser.py → BeautifulSoup footer copyright year extraction
            │
            ├── year found
            │       │
            │       ├── year < current_year - 5 → verdict='outdated'
            │       └── year >= current_year - 5 → verdict='current'
            │
            └── year NOT found
                    │
                    ▼
                wayback.py → CDX API query (15s timeout)
                    │
                    ├── CDX ok, captures exist, last < 2y → verdict='current'
                    ├── CDX ok, no recent captures → verdict='outdated'
                    └── CDX failed / timeout → verdict='unknown'
```

The enrichment loop is a simple `for business in unenriched_businesses` — no async, no threads.

---

## 5. Qualifier Design

The qualifier in `rules.py` is a collection of pure functions. The top-level function signature:

```python
def evaluate(business: Business, website_check: WebsiteCheck | None, config: Config) -> QualifierResult:
    ...

@dataclass
class QualifierResult:
    qualifies: bool | None   # True, False, or None (no_determinada)
    antigüedad_flag: str
    disqualify_reasons: list[str]
```

No database access happens inside `rules.py`. The repository layer fetches the data and passes it in. This makes the qualifier trivially testable with plain Python objects.

The dashboard applies the qualifier at query time by joining `businesses` with `website_checks` and filtering in pandas — no need for a pre-computed `prospect_qualifies` flag in v1 (add it as a materialized column in v2 if performance becomes an issue).

---

## 6. Streamlit Dashboard Design

### Session State

All filter values are stored in `st.session_state` using keys like `"filter_districts"`, `"filter_max_reviews"`, etc. This prevents filter resets on each Streamlit rerun.

### Data Loading

```python
@st.cache_data(ttl=300)  # 5-minute cache
def load_data(db_path: str) -> pd.DataFrame:
    # JOIN businesses + website_checks, apply qualifier logic in pandas
    ...
```

Cache TTL of 5 minutes means the dashboard won't reflect mid-scrape updates in real time (acceptable for v1).

### Excel Multi-Sheet Export

```python
def build_excel(df: pd.DataFrame, selected_districts: list[str]) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for district in selected_districts:
            sheet_df = df[df["district"] == district]
            if not sheet_df.empty:
                sheet_name = district[:31]  # Excel sheet name limit
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
    return buffer.getvalue()
```

The `st.download_button` receives the bytes object directly — no temp file needed.

---

## 7. Configuration Design

Config is loaded once at module import via `config.py`:

```python
from pydantic import BaseModel
import yaml

class Config(BaseModel):
    database: DatabaseConfig = DatabaseConfig()
    scraper: ScraperConfig = ScraperConfig()
    enrichment: EnrichmentConfig = EnrichmentConfig()
    qualifier: QualifierConfig = QualifierConfig()
    logging: LoggingConfig = LoggingConfig()

def load_config(path: str = "config.yaml") -> Config:
    if not os.path.exists(path):
        return Config()
    with open(path) as f:
        data = yaml.safe_load(f)
    return Config(**data)

CONFIG = load_config()
```

All modules import `CONFIG` from `config.py`. No module reads environment variables or files directly.

---

## 8. Error Handling and Resilience

| Layer | Strategy |
|-------|----------|
| Scraper — network error | Retry up to `max_retries` with exponential backoff; skip listing on persistent failure |
| Scraper — CAPTCHA detected | Wait 120s, retry once; stop run if still blocked |
| Scraper — listing parse error | Skip listing, log warning with place URL |
| Enrichment — HTTP timeout | Mark `verdict='unknown'`, continue |
| Enrichment — Wayback timeout | Mark `verdict='unknown'`, continue |
| DB — write error | Propagate and stop the run (data integrity priority) |
| Dashboard — DB not found | Show "No hay datos. Ejecuta el scraper primero." message |

All errors are logged via Python's `logging` module to both stderr and the configured log file. Log format: `%(asctime)s [%(levelname)s] %(name)s — %(message)s`.

---

## 9. Architecture Decision Records

### ADR-1: Playwright over Selenium

**Decision**: Use Playwright with `playwright-stealth`.
**Rationale**: Playwright has a modern async API, built-in auto-waiting for DOM elements, and better stealth plugin support. `playwright-stealth` patches the most common bot-detection signals at the browser level. Selenium with `undetected-chromedriver` is viable but slower and harder to maintain.
**Consequences**: Adds `playwright` and `playwright-stealth` as dependencies. Requires running `playwright install chromium` after pip install.

### ADR-2: SQLite over PostgreSQL

**Decision**: SQLite as the only database engine for v1.
**Rationale**: The dataset is bounded (estimated 500-3000 rows). SQLite is zero-ops — a single portable file, no server process, trivial backups (copy the file). SQLAlchemy abstracts the engine, so migrating to PostgreSQL later is a one-line config change.
**Consequences**: Only one writer at a time. WAL mode mitigates this for the read-while-scraping use case. Not suitable if multiple users need to run scrapers concurrently (not a v1 requirement).

### ADR-3: Streamlit over FastAPI + Vue

**Decision**: Streamlit as the dashboard framework.
**Rationale**: This is an internal research tool used by one person. Streamlit delivers a filterable table with export in hours, not days. The aesthetic limitations (full-page rerenders on filter change) are acceptable for datasets under 5000 rows.
**Consequences**: Dashboard is a Streamlit app, not a standalone REST API. If the tool needs to become a multi-user SaaS, a FastAPI + React rewrite is required. That is intentionally out of scope for v1.

### ADR-4: Sequential Districts, Not Parallel

**Decision**: Scrape districts one at a time, sequentially.
**Rationale**: Concurrent Google Maps requests from the same IP are the fastest path to a CAPTCHA block. The 30-60 second inter-district delay is not wasted time — it is the primary anti-detection mechanism. Parallelizing would require multiple proxied browser contexts, which is out of scope for v1.
**Consequences**: Full Lima scrape (43 districts × 3 keywords = 129 queries) takes approximately 2-4 hours. Acceptable for an overnight run.

### ADR-5: Selectors Centralized in selectors.py

**Decision**: All Google Maps DOM selectors live exclusively in `scraper/selectors.py`.
**Rationale**: Google updates the Maps UI 2-4 times per year. Each update potentially breaks selectors. Centralizing them means a DOM change requires editing exactly one file. Scattering selectors across the codebase would make updates error-prone and slow.
**Consequences**: `selectors.py` becomes a critical maintenance file. A smoke test on startup validates that key selectors still work, preventing silent data corruption.
