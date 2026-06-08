import json, os
import aiofiles
from pathlib import Path
from typing import Any

async def async_read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        text = await f.read()
    return json.loads(text) if text.strip() else default

async def async_write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    os.replace(tmp, path)
