from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from .models import Base
from lima_importadores.config import CONFIG


def _build_engine(db_path: str | None = None):
    path = db_path or CONFIG.database.path
    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
    return engine


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()
