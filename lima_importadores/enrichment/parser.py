import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_PATTERNS = [
    re.compile(r"©\s*(\d{4})"),
    re.compile(r"[Cc]opyright\s+(\d{4})"),
    re.compile(r"(\d{4})\s*©"),
    re.compile(r"(\d{4})\s+[Aa]ll\s+[Rr]ights"),
]

_FOOTER_CLASS_KEYWORDS = ("footer", "copyright", "copy")


def extract_copyright_year(html: str) -> int | None:
    """Parse the most recent copyright year found in the page footer area."""
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[str] = []

    footer = soup.find("footer")
    if footer:
        candidates.append(footer.get_text(" ", strip=True))

    for tag in soup.find_all(True):
        classes = " ".join(tag.get("class", []))
        if any(kw in classes.lower() for kw in _FOOTER_CLASS_KEYWORDS):
            candidates.append(tag.get_text(" ", strip=True))

    candidates.append(soup.get_text(" ", strip=True))

    years: list[int] = []
    for text in candidates:
        for pattern in _PATTERNS:
            for match in pattern.finditer(text):
                try:
                    years.append(int(match.group(1)))
                except ValueError:
                    pass

    if not years:
        return None

    year = max(years)
    logger.debug("Copyright year found: %d", year)
    return year
