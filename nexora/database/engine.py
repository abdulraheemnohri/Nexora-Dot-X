from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_engine = None
SessionFactory = None


def init_db(db_path: Path | None = None):
    """Create the engine and all tables. Idempotent."""
    global _engine, SessionFactory
    from nexora.config import settings
    path = db_path or settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{path}"
    _engine = create_engine(url, connect_args={"check_same_thread": False},
                            poolclass=StaticPool)
    from nexora.database import models  # noqa: F401  (registers mappers)
    from nexora.database.models import Base
    Base.metadata.create_all(_engine)
    SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def get_session_factory():
    if SessionFactory is None:
        init_db()
    return SessionFactory
