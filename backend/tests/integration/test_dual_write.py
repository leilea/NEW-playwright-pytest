"""Dual-write integration test — verifies that suite/case writes reach PostgreSQL."""
import pytest
import uuid


@pytest.mark.asyncio
async def test_pg_writer_suite_roundtrip(db_session):
    from app.services.pg_writer import write_suite_to_pg
    from app.models.catalog import Suite
    from sqlalchemy import select

    sid = str(uuid.uuid4())
    write_suite_to_pg({"id": sid, "name": "dw-suite", "version": "1.0"})

    result = await db_session.execute(
        select(Suite).where(Suite.legacy_id == sid)
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.name == "dw-suite"
    assert row.description == "1.0"


@pytest.mark.asyncio
async def test_pg_writer_suite_idempotent(db_session):
    from app.services.pg_writer import write_suite_to_pg
    from app.models.catalog import Suite
    from sqlalchemy import select, func

    sid = str(uuid.uuid4())
    write_suite_to_pg({"id": sid, "name": "dw-ido", "version": "v1"})
    write_suite_to_pg({"id": sid, "name": "dw-ido", "version": "v1"})

    result = await db_session.execute(
        select(func.count()).select_from(Suite).where(Suite.legacy_id == sid)
    )
    assert result.scalar() == 1
