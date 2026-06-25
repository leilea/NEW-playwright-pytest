import asyncio
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect

REC_SESSIONS: dict[str, WebSocket] = {}
REC_PROCS: dict[str, subprocess.Popen] = {}
REC_TASKS: dict[str, asyncio.Task] = {}

RECORDER_PROCESS = Path(__file__).resolve().parent.parent / "services" / "recorder_process.py"
_POOL = ThreadPoolExecutor(max_workers=2)


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
                task = asyncio.create_task(_run_recorder(session_id, url))
                REC_TASKS[session_id] = task
            elif cmd == "stop":
                proc = REC_PROCS.get(session_id)
                if proc and proc.returncode is None:
                    try:
                        proc.stdin.write(b'{"cmd":"stop"}\n')
                        proc.stdin.flush()
                    except Exception:
                        pass
                task = REC_TASKS.get(session_id)
                if task and not task.done():
                    try:
                        await asyncio.wait_for(task, timeout=10)
                    except asyncio.TimeoutError:
                        pass
                if session_id in REC_SESSIONS:
                    try:
                        await ws.send_json({"event": "stopped"})
                    except Exception:
                        pass
                break
    except WebSocketDisconnect:
        pass
    finally:
        REC_TASKS.pop(session_id, None)
        proc = REC_PROCS.pop(session_id, None)
        if proc and proc.returncode is None:
            try:
                proc.stdin.write(b'{"cmd":"stop"}\n')
                proc.stdin.flush()
            except Exception:
                pass
        REC_SESSIONS.pop(session_id, None)


async def _run_recorder(session_id: str, url: str):
    ws = REC_SESSIONS.get(session_id)
    if not ws:
        return
    loop = asyncio.get_running_loop()
    proc = await loop.run_in_executor(
        _POOL,
        lambda: subprocess.Popen(
            [sys.executable, "-X", "utf8", str(RECORDER_PROCESS)],
            env={**os.environ, "RECORDER_URL": url, "PYTHONUNBUFFERED": "1", "PYTHONUTF8": "1"},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        ),
    )
    REC_PROCS[session_id] = proc

    async def _read_stderr():
        try:
            while True:
                err_line = await loop.run_in_executor(_POOL, proc.stderr.readline)
                if not err_line:
                    break
                text = err_line.decode("utf-8", errors="replace").strip()
                if text:
                    print(f"[recorder stderr] {text}", flush=True)
        except Exception:
            pass

    asyncio.create_task(_read_stderr())

    step_count = 0
    try:
        while True:
            line = await loop.run_in_executor(_POOL, proc.stdout.readline)
            if not line:
                break
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            print(f"[rec ws] RAW: {text[:150]}", flush=True)
            try:
                data = json.loads(text)
            except json.JSONDecodeError as e:
                print(f"[rec ws] JSON_PARSE_ERR: {e} | raw={text[:120]}", flush=True)
                continue
            event = data.get("event", "")
            if event == "step":
                step = data["step"]
                action = step.get("action", "?")
                step_count += 1

                step_info = json.dumps(step, ensure_ascii=False)[:120]
                print(f"[rec ws] SEND #{step_count} {action}: {step_info}", flush=True)
                try:
                    await ws.send_json({"event": "step", "step": step})
                except Exception as e:
                    print(f"[rec ws] SEND_ERR: {e}", flush=True)
                    break
            elif event == "error":
                print(f"[rec ws] ERR: {data.get('message', '')[:120]}", flush=True)
                try:
                    await ws.send_json({"event": "error", "message": data.get("message", "")})
                except Exception:
                    break
            elif event == "done":
                print(f"[rec ws] DONE (total steps: {step_count})", flush=True)
                break
    except Exception as e:
        try:
            await ws.send_json({"event": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        REC_PROCS.pop(session_id, None)
        if proc.returncode is None:
            try:
                proc.stdin.write(b'{"cmd":"stop"}\n')
                proc.stdin.flush()
            except Exception:
                pass
            proc.terminate()
            proc.wait(timeout=5)
        try:
            await ws.send_json({"event": "done"})
        except Exception:
            pass
