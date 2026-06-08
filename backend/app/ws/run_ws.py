"""WebSocket handler: live Run log streaming."""
import json

from fastapi import WebSocket, WebSocketDisconnect


async def run_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            await ws.send_json({"type": "log", "text": f"[{msg.get('level','info')}] {msg.get('text','')}"})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
