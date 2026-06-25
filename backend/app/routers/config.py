import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.deps import get_current_user, get_db
from app.security.rbac import assert_can

router = APIRouter(tags=["config"], dependencies=[])
ENV_PATH = Path.cwd() / ".env"
CONFIG_DIR = Path.cwd() / "config"
REC_URL_FILE = CONFIG_DIR / "recording_url.json"
DEFAULT_REC_URL = "https://dsep-portal-test.minmetals.com.cn/portal/signin"


class ConfigPayload(BaseModel):
    content: str


class RecUrlPayload(BaseModel):
    url: str


@router.get("/config/env")
async def get_env(user=Depends(get_current_user), db=Depends(get_db)):
    await assert_can(user, "read", "config", db)
    if ENV_PATH.exists():
        return {"content": ENV_PATH.read_text(encoding="utf-8")}
    return {"content": ""}


@router.put("/config/env")
async def put_env(payload: ConfigPayload, user=Depends(get_current_user), db=Depends(get_db)):
    await assert_can(user, "write", "config", db)
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


@router.get("/config/recording-url")
async def get_recording_url(user=Depends(get_current_user), db=Depends(get_db)):
    await assert_can(user, "read", "config", db)
    if REC_URL_FILE.exists():
        data = json.loads(REC_URL_FILE.read_text("utf-8"))
        return {"url": data.get("url", DEFAULT_REC_URL)}
    return {"url": DEFAULT_REC_URL}


@router.put("/config/recording-url")
async def set_recording_url(payload: RecUrlPayload, user=Depends(get_current_user), db=Depends(get_db)):
    await assert_can(user, "write", "config", db)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    REC_URL_FILE.write_text(
        json.dumps({"url": payload.url}, ensure_ascii=False), encoding="utf-8"
    )
    return {"ok": True}
