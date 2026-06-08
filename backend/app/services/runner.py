import asyncio
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from app.config import settings

RUNS: dict[str, dict] = {}
_RUN_SINKS: dict[str, list[asyncio.Queue]] = {}


def get_sink(run_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _RUN_SINKS.setdefault(run_id, []).append(q)
    return q


async def watch_stream(stream, run_id: str, prefix: str):
    try:
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip("\n")
            entry = {"ts": datetime.now(timezone.utc).isoformat(), "text": text, "prefix": prefix}
            for q in _RUN_SINKS.get(run_id, []):
                await q.put(json.dumps(entry))
            logpath = Path(settings.log_dir) / f"{run_id}.log"
            logpath.parent.mkdir(parents=True, exist_ok=True)
            with open(logpath, "a", encoding="utf-8") as f:
                f.write(text + "\n")
    except Exception:
        pass


async def run_pytest(env: str, browser: str, suite_name: str, case_names: list[str] | None):
    run_id = uuid.uuid4().hex[:12]
    RUNS[run_id] = {"status": "running", "env": env, "browser": browser, "suite": suite_name, "started": datetime.now(timezone.utc).isoformat()}
    logpath = Path(settings.log_dir) / f"{run_id}.log"
    logpath.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "pytest", "tests/functional", "-v",
        f"--browser={browser}",
        f"--alluredir={settings.allure_results_dir}",
        f"--html={logpath.parent.parent / 'reports' / f'{run_id}.html'}",
        "--self-contained-html",
    ]
    if suite_name:
        marker = suite_name.replace(" ", "_").lower()
        cmd += ["-k", f"{marker} or {suite_name}"]
    if case_names:
        cmd += ["-k", " or ".join(case_names)]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=Path(__file__).resolve().parents[3],
    )
    await asyncio.gather(
        watch_stream(proc.stdout, run_id, "stdout"),
        watch_stream(proc.stderr, run_id, "stderr"),
    )
    rc = await proc.wait()
    RUNS[run_id]["status"] = "passed" if rc == 0 else "failed"
    RUNS[run_id]["exit_code"] = rc
    RUNS[run_id]["finished"] = datetime.now(timezone.utc).isoformat()
    return run_id
