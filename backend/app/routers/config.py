import os
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from app.deps import get_current_user
from app.security.rbac import assert_can

router = APIRouter(tags=["config"], dependencies=[])
ENV_PATH = Path.cwd() / ".env"


class ConfigPayload(BaseModel):
    content: str


@router.get("/config/env")
async def get_env(user=__import__("fastapi").Depends(get_current_user)):
    assert_can(user, "read", "config")
    if ENV_PATH.exists():
        return {"content": ENV_PATH.read_text(encoding="utf-8")}
    return {"content": ""}


@router.put("/config/env")
async def put_env(payload: ConfigPayload, user=__import__("fastapi").Depends(get_current_user)):
    assert_can(user, "write", "config")
    bak = ENV_PATH.with_suffix(".env.bak")
    if ENV_PATH.exists():
        bak.write_text(ENV_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    ENV_PATH.write_text(payload.content, encoding="utf-8")
    os.environ.clear()
    for line in payload.content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip()
    return {"ok": True}
