import asyncio
import logging
import random
import re
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus, urlparse, parse_qs

from playwright.async_api import BrowserContext, Page, TimeoutError as PWTimeout

from lima_importadores.config import ScraperConfig
from . import selectors

logger = logging.getLogger(__name__)

MAPS_SEARCH_URL = "https://www.google.com/maps/search/{query}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def scrape_query(
    context: BrowserContext,
    district: str,
    keyword: str,
    config: ScraperConfig,
) -> list[dict]:
    query = f"{keyword} {district} Peru"
    url = MAPS_SEARCH_URL.format(query=quote_plus(query))
    logger.info("Scraping: %s", query)

    page = await context.new_page()
    results: list[dict] = []
    errors = 0

    try:
        await page.goto(url, wait_until="load", timeout=30_000)
        logger.info("Landed on: %s", page.url)

        if await _captcha_detected(page):
            logger.warning("CAPTCHA on initial load for query: %s", query)
            await asyncio.sleep(120)
            await page.reload(wait_until="networkidle", timeout=30_000)
            if await _captcha_detected(page):
                logger.error("BLOCKED: CAPTCHA persists after retry — stopping")
                raise RuntimeError("CAPTCHA_BLOCKED")

        listing_count = await _scroll_and_collect(page, config)
        logger.info("Found %d listings for: %s", listing_count, query)

        for i in range(listing_count):
            # Close detail panel before re-querying to get fresh handles
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

            for attempt in range(config.max_retries + 1):
                try:
                    elements = await page.query_selector_all(selectors.LISTING_ITEM)
                    if i >= len(elements):
                        break
                    data = await _extract_listing(page, elements[i], district, config)
                    if data:
                        results.append(data)
                    break
                except Exception as exc:
                    if attempt < config.max_retries:
                        wait = min(
                            config.rate_limiting.retry_backoff_start * (2 ** attempt),
                            config.rate_limiting.retry_backoff_max,
                        )
                        logger.warning("Listing %d/%d error (retry %d): %s", i + 1, listing_count, attempt + 1, exc)
                        await asyncio.sleep(wait)
                    else:
                        logger.error("Listing %d/%d skipped after %d retries: %s", i + 1, listing_count, config.max_retries, exc)
                        errors += 1

            await asyncio.sleep(
                random.uniform(
                    config.rate_limiting.listing_delay_min,
                    config.rate_limiting.listing_delay_max,
                )
            )

    except RuntimeError:
        raise
    except Exception as exc:
        logger.error("Query failed: %s — %s", query, exc)
    finally:
        await page.close()

    return results


# ---------------------------------------------------------------------------
# Scroll and collect listing elements
# ---------------------------------------------------------------------------

async def _scroll_and_collect(page: Page, config: ScraperConfig) -> int:
    panel = await page.wait_for_selector(selectors.RESULTS_PANEL, timeout=30_000)
    prev_count = 0
    stale_scrolls = 0

    while True:
        items = await page.query_selector_all(selectors.LISTING_ITEM)
        count = len(items)

        if count >= config.max_listings_per_query:
            break

        if count == prev_count:
            stale_scrolls += 1
            if stale_scrolls >= 2:
                break
        else:
            stale_scrolls = 0

        prev_count = count
        await panel.evaluate("el => el.scrollBy(0, 800)")
        await asyncio.sleep(
            random.uniform(
                config.rate_limiting.scroll_delay_min,
                config.rate_limiting.scroll_delay_max,
            )
        )

    return len(await page.query_selector_all(selectors.LISTING_ITEM))


# ---------------------------------------------------------------------------
# Per-listing extraction
# ---------------------------------------------------------------------------

async def _extract_listing(
    page: Page,
    element,
    seed_district: str,
    config: ScraperConfig,
) -> dict | None:
    # Capture place URL from listing anchor BEFORE clicking (avoids page.url timing issues)
    anchor = await element.query_selector('a[href*="/maps/place/"]')
    pre_href = await anchor.get_attribute("href") if anchor else None

    await element.click()
    await page.wait_for_selector(selectors.DETAIL_NAME, timeout=10_000)
    await asyncio.sleep(0.5)

    name = await _text(page, selectors.DETAIL_NAME)
    logger.info("Extracting: name=%s", name)
    if not name:
        return None

    address = await _text(page, selectors.DETAIL_ADDRESS)
    phone = await _text(page, selectors.DETAIL_PHONE)
    category = await _text(page, selectors.DETAIL_CATEGORY)

    website_url = None
    website_el = await page.query_selector(selectors.DETAIL_WEBSITE)
    if website_el:
        website_url = await website_el.get_attribute("href")

    rating = None
    rating_el = await page.query_selector(selectors.DETAIL_RATING)
    if rating_el:
        raw = await rating_el.inner_text()
        rating = _parse_float(raw.replace(",", "."))

    review_count = 0
    rc_el = await page.query_selector(selectors.DETAIL_REVIEW_COUNT)
    if rc_el:
        aria = await rc_el.get_attribute("aria-label") or ""
        review_count = _parse_review_count(aria)

    place_id, lat, lng = _parse_url(pre_href or page.url)
    district = _parse_district(address, config.districts) or seed_district
    oldest_review_date = await _extract_oldest_review_date(page)

    return {
        "place_id": place_id or name,
        "name": name,
        "address": address,
        "district": district,
        "phone": phone,
        "website_url": website_url,
        "has_website": website_url is not None,
        "rating": rating,
        "review_count": review_count,
        "category": category,
        "latitude": lat,
        "longitude": lng,
        "oldest_review_date": oldest_review_date,
        "antiguedad_flag": "no_determinada",
        "prospect_qualifies": None,
        "scraped_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Oldest review date
# ---------------------------------------------------------------------------

async def _extract_oldest_review_date(page: Page) -> str | None:
    review_els = await page.query_selector_all(selectors.REVIEW_ITEMS)
    if not review_els:
        return None

    dates: list[date] = []
    today = date.today()

    for el in review_els:
        date_el = await el.query_selector(selectors.REVIEW_DATE)
        if not date_el:
            continue
        text = (await date_el.inner_text() or "").strip().lower()
        parsed = _parse_review_date(text, today)
        if parsed:
            dates.append(parsed)

    if not dates:
        return None
    return min(dates).isoformat()


def _parse_review_date(text: str, today: date) -> date | None:
    # "hace N años" / "hace N meses" / "hace N semanas"
    m = re.search(r"hace\s+(\d+)\s+(año|años|mes|meses|semana|semanas)", text)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if "año" in unit:
            return date(today.year - n, today.month, today.day)
        if "mes" in unit:
            return (today - timedelta(days=n * 30)).replace(day=1)
        if "semana" in unit:
            return today - timedelta(weeks=n)

    # "enero de 2019" / "mayo 2018"
    MONTHS = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    m2 = re.search(r"(\w+)\s+(?:de\s+)?(\d{4})", text)
    if m2:
        month_name = m2.group(1)
        year = int(m2.group(2))
        month = MONTHS.get(month_name)
        if month:
            return date(year, month, 1)

    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _text(page: Page, selector: str) -> str | None:
    el = await page.query_selector(selector)
    if not el:
        return None
    text = (await el.inner_text() or "").strip()
    return text or None


def _parse_float(s: str) -> float | None:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _parse_review_count(aria_label: str) -> int:
    m = re.search(r"([\d,\.]+)", aria_label)
    if m:
        return int(re.sub(r"[,\.]", "", m.group(1)))
    return 0


def _parse_url(url: str) -> tuple[str | None, float | None, float | None]:
    place_id = None
    lat = lng = None

    m = re.search(r"!1s([^!]+)", url)
    if m:
        place_id = m.group(1)

    # Format @lat,lng (from page.url after navigation)
    m2 = re.search(r"@(-?[\d.]+),(-?[\d.]+)", url)
    if m2:
        try:
            lat = float(m2.group(1))
            lng = float(m2.group(2))
        except ValueError:
            pass

    # Fallback format !3dLAT!4dLNG (from listing anchor href)
    if lat is None or lng is None:
        m3 = re.search(r"!3d(-?[\d.]+)", url)
        m4 = re.search(r"!4d(-?[\d.]+)", url)
        if m3 and m4:
            try:
                lat = float(m3.group(1))
                lng = float(m4.group(1))
            except ValueError:
                pass

    return place_id, lat, lng


def _parse_district(address: str | None, districts: list[str]) -> str | None:
    if not address:
        return None
    address_lower = address.lower()
    for d in districts:
        if d.lower() in address_lower:
            return d
    return None


async def _captcha_detected(page: Page) -> bool:
    captcha = await page.query_selector(selectors.CAPTCHA_FORM)
    recaptcha = await page.query_selector(selectors.RECAPTCHA_FRAME)
    return captcha is not None or recaptcha is not None
