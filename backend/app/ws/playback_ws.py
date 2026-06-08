"""WebSocket handler: real-time Playback streaming."""
import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect

from app.services import playback as pb


async def playback_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        raw = await ws.receive_text()
        cmd = json.loads(raw)
        action = cmd.get("action")

        if action == "start":
            result = await pb.run_playback(
                case_name=cmd.get("case_name", "unnamed"),
                steps=cmd.get("steps", []),
                browser=cmd.get("browser", "chromium"),
                ws_token=id(ws).to_bytes(4).hex(),
            )
            await ws.send_json({"type": "done", **result})
        else:
            await ws.send_json({"type": "error", "text": f"unknown action: {action}"})
    except WebSocketDisconnect:
        pass
    except Exception:
        await ws.send_json({"type": "error", "text": "internal error"})
