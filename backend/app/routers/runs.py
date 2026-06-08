import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from pydantic import BaseModel
from app.deps import get_current_user
from app.services.runner import run_pytest, RUNS, get_sink

router = APIRouter(tags=["runs"])
_active_sockets: dict[str, list[WebSocket]] = {}


class RunRequest(BaseModel):
    env: str = "test"
    browser: str = "chromium"
    suite_name: str = ""
    case_names: list[str] | None = None


@router.post("/runs")
async def start_run(req: RunRequest, user=Depends(get_current_user)):
    run_id = await run_pytest(req.env, req.browser, req.suite_name, req.case_names)
    return {"run_id": run_id, "status": "running"}


@router.get("/runs")
async def list_runs():
    return [
        {"id": rid, **info}
        for rid, info in sorted(RUNS.items(), key=lambda x: x[1].get("started", ""), reverse=True)[:100]
    ]


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    if run_id not in RUNS:
        return {"error": "not found"}
    return {"id": run_id, **RUNS[run_id]}


@router.websocket("/ws/run/{run_id}")
async def ws_run(websocket: WebSocket, run_id: str):
    await websocket.accept()
    _active_sockets.setdefault(run_id, []).append(websocket)
    q = get_sink(run_id)
    try:
        while True:
            msg = await q.get()
            for ws in _active_sockets.get(run_id, []):
                try:
                    await ws.send_text(msg)
                except Exception:
                    pass
    except WebSocketDisconnect:
        _active_sockets.get(run_id, []).remove(websocket)
