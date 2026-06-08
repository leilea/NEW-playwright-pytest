import pytest


@pytest.mark.asyncio
async def test_list_suites_empty(client, db_session):
    r = await client.get("/api/suites")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_suite_returns_201(client, db_session):
    r = await client.post("/api/suites", json={"name": "s1"})
    assert r.status_code == 201
    assert r.json()["name"] == "s1"
