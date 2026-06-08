"""Verify data consistency between legacy JSON files and PostgreSQL."""
import asyncio, json
from pathlib import Path
from sqlalchemy import select, func
from app.db.session import session_scope
from app.models.catalog import Suite, Case
from lib_compat.json_store_async import async_read_json


async def verify():
    s_json = await async_read_json(Path("logs/suites.json"), default=[])
    c_json = await async_read_json(Path("logs/testcases.json"), default=[])
    async with session_scope() as db:
        s_pg = (await db.execute(select(func.count()).select_from(Suite))).scalar()
        c_pg = (await db.execute(select(func.count()).select_from(Case))).scalar()
    return {
        "suites": {"json": len(s_json), "pg": s_pg},
        "cases": {"json": len(c_json), "pg": c_pg},
        "ok": len(s_json) == s_pg and len(c_json) == c_pg,
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(verify()), indent=2))
