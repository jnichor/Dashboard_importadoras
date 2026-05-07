import logging
from datetime import date, datetime
import requests

logger = logging.getLogger(__name__)

CDX_API = "https://web.archive.org/cdx/search/cdx"


def get_last_capture(url: str, timeout: int) -> date | None:
    """Return the date of the most recent Wayback Machine capture, or None."""
    params = {
        "url": url,
        "output": "json",
        "limit": 1,
        "fl": "timestamp",
        "from": "20200101",
        "filter": "statuscode:200",
        "fastLatest": "true",
    }
    try:
        resp = requests.get(CDX_API, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        # data is [["timestamp"], ["YYYYMMDDHHmmss"]] or [["timestamp"]] (header only)
        if len(data) < 2:
            logger.debug("No Wayback captures for: %s", url)
            return None
        timestamp = data[1][0]
        return datetime.strptime(timestamp[:8], "%Y%m%d").date()
    except Exception as exc:
        logger.warning("Wayback CDX error for %s: %s", url, exc)
        return None
