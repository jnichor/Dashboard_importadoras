from dataclasses import dataclass, field
from datetime import date, timedelta

from lima_importadores.config import QualifierConfig
from lima_importadores.storage.models import Business, WebsiteCheck


@dataclass
class QualifierResult:
    qualifies: bool | None  # True, False, or None (no_determinada)
    antiguedad_flag: str
    disqualify_reasons: list[str] = field(default_factory=list)


def evaluate(
    business: Business,
    website_check: WebsiteCheck | None,
    config: QualifierConfig,
    districts: list[str],
    keywords: list[str],
) -> QualifierResult:
    reasons: list[str] = []

    # Criterion 1 — Sector
    if not _matches_sector(business, keywords):
        reasons.append("sector_no_match")

    # Criterion 2 — Location
    if not business.district or business.district not in districts:
        reasons.append("district_out_of_scope" if business.district else "district_unknown")

    # Criterion 3 — Antigüedad
    antiguedad_flag = _evaluate_antiguedad(business, config.antigüedad_years)

    # Criterion 4 — Low reviews
    if business.review_count >= config.max_review_count + 1:
        reasons.append("too_many_reviews")

    # Criterion 5 — Rating
    if business.rating is not None and business.rating < config.min_rating:
        reasons.append("low_rating")

    # Criterion 6 — Weak web presence
    if not _has_weak_presence(business, website_check):
        reasons.append("website_current")

    if reasons:
        return QualifierResult(qualifies=False, antiguedad_flag=antiguedad_flag, disqualify_reasons=reasons)

    if antiguedad_flag == "no_determinada":
        return QualifierResult(qualifies=None, antiguedad_flag=antiguedad_flag)

    return QualifierResult(qualifies=True, antiguedad_flag=antiguedad_flag)


# ---------------------------------------------------------------------------
# Criterion helpers
# ---------------------------------------------------------------------------

def _matches_sector(business: Business, keywords: list[str]) -> bool:
    text = " ".join(filter(None, [business.name, business.category])).lower()
    if not text.strip():
        return False
    return any(kw.lower() in text for kw in keywords)


def _evaluate_antiguedad(business: Business, years_threshold: int) -> str:
    if business.review_count == 0:
        return "califica"
    if business.oldest_review_date:
        try:
            oldest = date.fromisoformat(business.oldest_review_date)
            cutoff = date.today() - timedelta(days=years_threshold * 365)
            return "califica" if oldest <= cutoff else "no_determinada"
        except ValueError:
            pass
    return "no_determinada"


def _has_weak_presence(business: Business, website_check: WebsiteCheck | None) -> bool:
    if not business.has_website:
        return True
    if website_check is None:
        return True  # not yet checked — benefit of the doubt
    return website_check.verdict in ("outdated", "no_site", "unknown")


def apply_qualifier_to_all(session, config, districts: list[str], keywords: list[str]) -> int:
    """Evaluate all businesses and persist results. Returns count of qualified prospects."""
    from lima_importadores.storage.models import Business, WebsiteCheck

    businesses = session.query(Business).all()
    qualified = 0

    for business in businesses:
        wc = (
            session.query(WebsiteCheck)
            .filter_by(place_id=business.place_id)
            .first()
        )
        result = evaluate(business, wc, config, districts, keywords)

        business.antiguedad_flag = result.antiguedad_flag
        business.prospect_qualifies = (
            1 if result.qualifies is True
            else 0 if result.qualifies is False
            else None
        )
        business.disqualify_reason = (
            ", ".join(result.disqualify_reasons) if result.disqualify_reasons else None
        )
        if result.qualifies is True:
            qualified += 1

    session.commit()
    return qualified
