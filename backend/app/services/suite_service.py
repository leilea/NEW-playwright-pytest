from sqlalchemy import select
from app.models.catalog import Suite

async def create_suite(db, *, name, description="", owner_id=None) -> Suite:
    s = Suite(name=name, description=description, owner_id=owner_id)
    db.add(s); await db.flush(); await db.refresh(s)
    return s

async def list_suites(db) -> list[Suite]:
    res = await db.execute(select(Suite).order_by(Suite.id))
    return list(res.scalars())

async def get_suite(db, suite_id: int) -> Suite | None:
    return (await db.execute(select(Suite).where(Suite.id == suite_id))).scalar_one_or_none()

async def update_suite(db, suite_id: int, **fields) -> Suite | None:
    s = await get_suite(db, suite_id)
    if not s: return None
    for k, v in fields.items():
        if v is not None and hasattr(s, k): setattr(s, k, v)
    await db.flush(); await db.refresh(s)
    return s

async def delete_suite(db, suite_id: int) -> bool:
    s = await get_suite(db, suite_id)
    if not s: return False
    await db.delete(s); await db.flush()
    return True
