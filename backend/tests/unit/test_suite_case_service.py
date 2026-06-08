import pytest
from app.services.suite_service import create_suite, list_suites
from app.services.case_service import create_case, add_step
from app.models.auth import User

@pytest.mark.asyncio
async def test_create_and_list_suite(db_session):
    u = User(email="o@e.c"); db_session.add(u); await db_session.flush()
    s = await create_suite(db_session, name="login", description="", owner_id=u.id)
    suites = await list_suites(db_session)
    assert any(x.id == s.id for x in suites)

@pytest.mark.asyncio
async def test_case_steps_roundtrip(db_session):
    u = User(email="o@e.c"); db_session.add(u); await db_session.flush()
    s = await create_suite(db_session, name="s", owner_id=u.id)
    c = await create_case(db_session, suite_id=s.id, name="t1", tags=["smoke"], owner_id=u.id)
    c = await add_step(db_session, case_id=c.id, step={"action": "goto", "value": "https://x"})
    assert c.steps[-1]["action"] == "goto"
