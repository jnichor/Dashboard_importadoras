from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from .models import Base
from lima_importadores.config import CONFIG


def _build_engine():
    """Construye el engine de SQLAlchemy.

    Si CONFIG.database.url esta seteado (via env DATABASE_URL), usa Postgres.
    Si no, cae al SQLite local definido por CONFIG.database.path (legacy).
    """
    if CONFIG.database.url:
        return create_engine(
            CONFIG.database.url,
            pool_pre_ping=True,
        )

    engine = create_engine(
        f"sqlite:///{CONFIG.database.path}",
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
