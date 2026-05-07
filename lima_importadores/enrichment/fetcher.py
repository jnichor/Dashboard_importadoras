import logging
import requests

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def fetch_url(url: str, timeout: int, max_redirects: int) -> tuple[int | None, str | None]:
    """Return (http_status, html) or (None, None) on any error."""
    try:
        session = requests.Session()
        session.max_redirects = max_redirects
        resp = session.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        return resp.status_code, resp.text
    except requests.TooManyRedirects:
        logger.warning("Too many redirects: %s", url)
        return None, None
    except requests.Timeout:
        logger.warning("Timeout fetching: %s", url)
        return None, None
    except Exception as exc:
        logger.warning("Fetch error for %s: %s", url, exc)
        return None, None
