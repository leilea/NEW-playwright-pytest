"""WebSocket handler: real-time Playback streaming."""
import asyncio
import json
import logging
import traceback

from fastapi import WebSocket, WebSocketDisconnect

from app.services import playback as pb


async def playback_ws(ws: WebSocket) -> None:
    await ws.accept()
    print("[playback_ws] connected", flush=True)
    try:
        raw = await ws.receive_text()
        print(f"[playback_ws] received: {raw[:200]}", flush=True)
        cmd = json.loads(raw)
        action = cmd.get("action")
        print(f"[playback_ws] action={action}, steps={len(cmd.get('steps',[]))}", flush=True)

        if action == "start":
            print("[playback_ws] calling run_playback...", flush=True)
            result = await pb.run_playback(
                case_name=cmd.get("case_name", "unnamed"),
                steps=cmd.get("steps", []),
                browser=cmd.get("browser", "chromium"),
                ws_token=str(id(ws)),
            )
            print(f"[playback_ws] result: rc={result.get('rc')}", flush=True)
            full_stdout = result.get('stdout','')
            # show FAILURES section
            import re
            for m in re.finditer(r'(?:FAILURES|ERRORS).*?(?=FAILED|$)', full_stdout, re.S):
                print(f"[playback_ws] FAILURE: {m.group()[:1000]}", flush=True)
            print(f"[playback_ws] STDOUT tail: {full_stdout[-500:]}", flush=True)
            print(f"[playback_ws] STDERR tail: {result.get('stderr','')[-500:]}", flush=True)
            await ws.send_json({"type": "done", **result})
            print("[playback_ws] response sent", flush=True)
        else:
            await ws.send_json({"type": "error", "text": f"unknown action: {action}"})
    except WebSocketDisconnect:
        print("[playback_ws] WebSocketDisconnect", flush=True)
    except Exception as e:
        print(f"[playback_ws] error: {e}", flush=True)
        traceback.print_exc()
        try:
            await ws.send_json({"type": "error", "text": str(e)})
        except Exception:
            pass
