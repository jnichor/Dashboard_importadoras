import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .models import Business, WebsiteCheck, ScrapeRun, CallOutcome


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dialect_insert(session: Session):
    """Devuelve la funcion `insert` correcta segun el dialecto activo."""
    if session.get_bind().dialect.name == "postgresql":
        return pg_insert
    return sqlite_insert


def upsert_business(session: Session, data: dict) -> Business:
    insert_fn = _dialect_insert(session)
    stmt = (
        insert_fn(Business)
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
    insert_fn = _dialect_insert(session)
    stmt = (
        insert_fn(WebsiteCheck)
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


def upsert_call_outcome(
    session: Session,
    place_id: str,
    contacted: str,
    response: str | None = None,
    notes: str | None = None,
) -> CallOutcome:
    """Inserta o actualiza el resultado de llamada para un place_id.

    contacted: 'no_llamado' | 'contesto' | 'no_contesto'
    response:  'acepto' | 'rechazo' | 'pendiente' | None
    """
    insert_fn = _dialect_insert(session)
    now = _now()
    data = {
        "place_id": place_id,
        "contacted": contacted,
        "response": response,
        "notes": notes,
        "called_at": now,
        "updated_at": now,
    }
    stmt = (
        insert_fn(CallOutcome)
        .values(**data)
        .on_conflict_do_update(
            index_elements=["place_id"],
            set_={
                "contacted": contacted,
                "response": response,
                "notes": notes,
                "called_at": now,
                "updated_at": now,
            },
        )
    )
    session.execute(stmt)
    session.flush()
    return session.query(CallOutcome).filter_by(place_id=place_id).one()
