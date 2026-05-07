import logging
from playwright.async_api import Playwright, BrowserContext, Page

from . import selectors

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

SMOKE_TEST_URL = "https://www.google.com/maps"


async def create_browser_context(playwright: Playwright) -> BrowserContext:
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1280, "height": 900},
        locale="es-PE",
        timezone_id="America/Lima",
    )
    return context


async def run_smoke_test(context: BrowserContext) -> bool:
    """Verify that key selectors still work against the Maps homepage."""
    page = await context.new_page()
    try:
        await page.goto(SMOKE_TEST_URL, wait_until="domcontentloaded", timeout=30_000)
        try:
            await page.wait_for_selector(selectors.SEARCH_BOX, timeout=15_000)
        except Exception:
            logger.error("SELECTOR_STALE: search box not found on Maps homepage")
            return False
        logger.info("Smoke test passed — selectors look healthy")
        return True
    except Exception as exc:
        logger.error("Smoke test failed: %s", exc)
        return False
    finally:
        await page.close()
