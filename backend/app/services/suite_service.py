from sqlalchemy import select, func
from app.models.catalog import Suite, Case

async def create_suite(db, *, name, version="", description="", owner_id=None) -> Suite:
    s = Suite(name=name, version=version, description=description, owner_id=owner_id)
    db.add(s); await db.flush(); await db.refresh(s)
    return s

async def list_suites(db) -> list[Suite]:
    case_count_subq = (
        select(Case.suite_id, func.count(Case.id).label("cnt"))
        .group_by(Case.suite_id)
        .subquery()
    )
    res = await db.execute(
        select(Suite, case_count_subq.c.cnt)
        .outerjoin(case_count_subq, Suite.id == case_count_subq.c.suite_id)
        .order_by(Suite.id)
    )
    rows = res.all()
    for suite, cnt in rows:
        suite.case_count = cnt or 0
    return [suite for suite, _ in rows]

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
