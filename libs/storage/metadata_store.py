"""Postgres metadata store using SQLAlchemy Core (async-friendly session factory)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from libs.common.settings import get_settings


def _make_engine():
    settings = get_settings()
    return create_engine(
        settings.postgres_dsn,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


_engine = None
_SessionLocal: sessionmaker | None = None


def _get_session_factory() -> sessionmaker:
    global _engine, _SessionLocal
    if _SessionLocal is None:
        _engine = _make_engine()
        _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager that provides a transactional database session.

    Usage::

        with get_session() as db:
            db.execute(text("SELECT 1"))
    """
    factory = _get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def healthcheck() -> bool:
    """Return True if the database is reachable."""
    try:
        with get_session() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
