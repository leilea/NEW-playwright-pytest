from sqlalchemy import select
from app.models.catalog import Case

async def create_case(db, *, suite_id, name, tags=None, steps=None, parameters=None, owner_id=None) -> Case:
    c = Case(suite_id=suite_id, name=name, tags=tags or [], steps=steps or [], parameters=parameters or [], owner_id=owner_id)
    db.add(c); await db.flush(); await db.refresh(c)
    return c

async def get_case(db, case_id: int) -> Case | None:
    return (await db.execute(select(Case).where(Case.id == case_id))).scalar_one_or_none()

async def list_cases(db, suite_id: int | None = None) -> list[Case]:
    q = select(Case).order_by(Case.id)
    if suite_id is not None: q = q.where(Case.suite_id == suite_id)
    return list((await db.execute(q)).scalars())

async def add_step(db, *, case_id: int, step: dict) -> Case:
    c = await get_case(db, case_id)
    assert c, "case not found"
    steps = list(c.steps or [])
    steps.append(step)
    c.steps = steps
    await db.flush(); await db.refresh(c)
    return c

async def update_case_steps(db, *, case_id: int, steps: list[dict], parameters: list[dict] | None = None) -> Case:
    c = await get_case(db, case_id)
    assert c, "case not found"
    c.steps = steps
    if parameters is not None:
        c.parameters = parameters
    await db.flush(); await db.refresh(c)
    return c

async def delete_case(db, case_id: int) -> bool:
    c = await get_case(db, case_id)
    if not c: return False
    await db.delete(c); await db.flush()
    return True
