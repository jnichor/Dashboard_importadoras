import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .models import Business, WebsiteCheck, ScrapeRun


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_business(session: Session, data: dict) -> Business:
    stmt = (
        sqlite_insert(Business)
        .values(**data)
        .on_conflict_do_update(
            index_elements=["place_id"],
            set_={k: v for k, v in data.items() if k != "place_id"},
        )
    )
    session.execute(stmt)
    session.flush()
    return session.query(Business).filter_by(place_id=data["place_id"]).one()


def upsert_website_check(session: Session, data: dict) -> WebsiteCheck:
    stmt = (
        sqlite_insert(WebsiteCheck)
        .values(**data)
        .on_conflict_do_update(
            index_elements=["place_id"],
            set_={k: v for k, v in data.items() if k != "place_id"},
        )
    )
    session.execute(stmt)
    session.flush()
    return session.query(WebsiteCheck).filter_by(place_id=data["place_id"]).one()


def create_scrape_run(
    session: Session,
    districts: list[str],
    keywords: list[str],
) -> ScrapeRun:
    run = ScrapeRun(
        started_at=_now(),
        districts_queried=json.dumps(districts, ensure_ascii=False),
        keywords_used=json.dumps(keywords, ensure_ascii=False),
        businesses_found=0,
        errors=0,
    )
    session.add(run)
    session.flush()
    return run


def complete_scrape_run(
    session: Session,
    run: ScrapeRun,
    businesses_found: int,
    errors: int,
) -> None:
    run.completed_at = _now()
    run.businesses_found = businesses_found
    run.errors = errors
    session.flush()


def get_unenriched_businesses(session: Session) -> list[Business]:
    checked_ids = session.query(WebsiteCheck.place_id)
    return (
        session.query(Business)
        .filter(Business.has_website == True)
        .filter(Business.place_id.not_in(checked_ids))
        .all()
    )
