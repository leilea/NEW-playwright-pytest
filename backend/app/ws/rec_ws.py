import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from app.services.recorder import start_codegen

REC_SESSIONS: dict[str, WebSocket] = {}

async def rec_ws(ws: WebSocket):
    await ws.accept()
    session_id = str(id(ws))
    REC_SESSIONS[session_id] = ws

    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)
            cmd = data.get("cmd")

            if cmd == "start":
                url = data.get("url", "")
                proc = asyncio.create_task(_run_recorder(session_id, url))
            elif cmd == "stop":
                if session_id in REC_SESSIONS:
                    await ws.send_json({"event": "stopped"})
                break
    except WebSocketDisconnect:
        pass
    finally:
        REC_SESSIONS.pop(session_id, None)


async def _run_recorder(session_id: str, url: str):
    ws = REC_SESSIONS.get(session_id)
    if not ws:
        return
    try:
        async for step in start_codegen(url):
            try:
                await ws.send_json({"event": "step", "step": step})
            except Exception:
                break
    except Exception as e:
        try:
            await ws.send_json({"event": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await ws.send_json({"event": "done"})
        except Exception:
            pass
