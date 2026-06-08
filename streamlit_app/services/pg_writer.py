"""PG writer wrapper — Streamlit sync context writes to PostgreSQL via dual-write layer.
Graceful fallback: if DUAL_WRITE_DSN is not set, all functions are no-ops.
"""
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from app.db.base import Base
from app import models  # noqa: F401 — register model metadata

_DSN = os.environ.get("DUAL_WRITE_DSN") or os.environ.get("DATABASE_URL", "").replace("+asyncpg", "+psycopg2")
_engine = None
_SessionFactory = None


def _ensure_session() -> Session | None:
    global _engine, _SessionFactory
    if not _DSN:
        return None
    if _SessionFactory is None:
        _engine = create_engine(_DSN, pool_pre_ping=True, future=True)
        _SessionFactory = sessionmaker(_engine, expire_on_commit=False, future=True)
    return _SessionFactory()


def write_suite_to_pg(suite_dict: dict) -> int | None:
    """Insert or update a suite in PG. Uses legacy_id (Streamlit UUID) as lookup key."""
    if not _DSN:
        return None
    from app.models.catalog import Suite
    legacy_id = suite_dict.get("id")
    with _ensure_session() as s:
        existing = None
        if legacy_id:
            existing = s.execute(
                select(Suite).where(Suite.legacy_id == legacy_id)
            ).scalar_one_or_none()
        if existing:
            existing.name = suite_dict.get("name", existing.name)
            existing.description = suite_dict.get("version", existing.description)
        else:
            existing = Suite(
                legacy_id=legacy_id,
                name=suite_dict.get("name", ""),
                description=suite_dict.get("version", ""),
            )
            s.add(existing)
        s.commit()
        return existing.id


def write_case_to_pg(case_dict: dict) -> int | None:
    """Insert or update a case in PG. Uses legacy_id (Streamlit UUID) as lookup key."""
    if not _DSN:
        return None
    from app.models.catalog import Case, Suite
    legacy_id = case_dict.get("id")
    suite_legacy_id = case_dict.get("suite_id")
    with _ensure_session() as s:
        existing = None
        if legacy_id:
            existing = s.execute(
                select(Case).where(Case.legacy_id == legacy_id)
            ).scalar_one_or_none()
        if existing:
            existing.name = case_dict.get("name", existing.name)
            existing.tags = case_dict.get("tags") or []
            existing.steps = case_dict.get("steps") or []
        else:
            suite_pg_id = None
            if suite_legacy_id:
                suite = s.execute(
                    select(Suite).where(Suite.legacy_id == suite_legacy_id)
                ).scalar_one_or_none()
                if suite:
                    suite_pg_id = suite.id
            existing = Case(
                legacy_id=legacy_id,
                suite_id=suite_pg_id if suite_pg_id else 0,
                name=case_dict.get("name", ""),
                tags=case_dict.get("tags") or [],
                steps=case_dict.get("steps") or [],
            )
            s.add(existing)
        s.commit()
        return existing.id
