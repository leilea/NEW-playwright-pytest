import pytest, tempfile, json
from pathlib import Path
from lib_compat.json_store_async import async_read_json, async_write_json_atomic

@pytest.mark.asyncio
async def test_read_missing_returns_default():
    p = Path(tempfile.mkdtemp()) / "nope.json"
    assert await async_read_json(p, default={}) == {}

@pytest.mark.asyncio
async def test_write_atomic_creates_file():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.json"
        await async_write_json_atomic(p, {"a": 1})
        assert json.loads(p.read_text()) == {"a": 1}
