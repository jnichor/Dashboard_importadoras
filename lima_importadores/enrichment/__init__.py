import logging
from datetime import date, timedelta

from lima_importadores.config import EnrichmentConfig
from lima_importadores.storage.models import Business
from .fetcher import fetch_url
from .parser import extract_copyright_year
from .wayback import get_last_capture

logger = logging.getLogger(__name__)


def enrich_business(business: Business, config: EnrichmentConfig) -> dict:
    """Run the enrichment pipeline for one business. Returns a dict for WebsiteCheck."""
    now = date.today().isoformat()

    if not business.has_website or not business.website_url:
        return _make_check(business, verdict="no_site", checked_at=now)

    status, html = fetch_url(
        business.website_url,
        timeout=config.request_timeout,
        max_redirects=config.max_redirects,
    )

    if status is None or html is None:
        return _make_check(business, verdict="unknown", http_status=status, checked_at=now)

    copyright_year = extract_copyright_year(html)
    cutoff_year = date.today().year - config.outdated_threshold_years

    if copyright_year is not None:
        verdict = "outdated" if copyright_year <= cutoff_year else "current"
        return _make_check(
            business,
            verdict=verdict,
            http_status=status,
            copyright_year=copyright_year,
            checked_at=now,
        )

    # No copyright year found — try Wayback CDX fallback
    last_capture = get_last_capture(business.website_url, timeout=config.wayback_timeout)

    if last_capture is None:
        return _make_check(business, verdict="unknown", http_status=status, checked_at=now)

    two_years_ago = date.today() - timedelta(days=730)
    verdict = "current" if last_capture >= two_years_ago else "outdated"
    return _make_check(
        business,
        verdict=verdict,
        http_status=status,
        wayback_last_capture=last_capture.isoformat(),
        checked_at=now,
    )


def run_enrichment(session, config: EnrichmentConfig) -> int:
    """Enrich all businesses not yet checked. Returns count of processed businesses."""
    from lima_importadores.storage.repository import get_unenriched_businesses, upsert_website_check
    from datetime import datetime, timezone

    businesses = get_unenriched_businesses(session)
    logger.info("Enriching %d businesses", len(businesses))

    for i, business in enumerate(businesses, 1):
        logger.debug("[%d/%d] Enriching: %s", i, len(businesses), business.name)
        data = enrich_business(business, config)
        upsert_website_check(session, data)

    session.commit()
    return len(businesses)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_check(
    business: Business,
    verdict: str,
    http_status: int | None = None,
    copyright_year: int | None = None,
    wayback_last_capture: str | None = None,
    checked_at: str = "",
) -> dict:
    from datetime import datetime, timezone
    return {
        "business_id": business.id,
        "place_id": business.place_id,
        "http_status": http_status,
        "copyright_year": copyright_year,
        "wayback_last_capture": wayback_last_capture,
        "verdict": verdict,
        "checked_at": checked_at or datetime.now(timezone.utc).isoformat(),
    }
