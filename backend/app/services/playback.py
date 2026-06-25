"""PlaybackService — run a recorded test case via Playwright subprocess."""
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings


async def run_playback(case_name: str, steps: list[dict], browser: str, ws_token: str) -> dict:
    """Execute steps via playwright subprocess. Returns summary dict."""
    sid = uuid.uuid4().hex[:8]
    script = _build_playwright_script(sid, case_name, steps, browser)
    temp_root = Path(os.environ.get("TEMP", tempfile.gettempdir()))
    path = temp_root / f"playback_{sid}.py"
    path.write_text(script, encoding="utf-8")
    print(f"[playback] script={path}  size={len(script)}", flush=True)

    started_at = datetime.now(timezone.utc)
    loop = asyncio.get_running_loop()
    proc = await loop.run_in_executor(
        None,
        lambda: subprocess.Popen(
            [sys.executable, "-X", "utf8", "-m", "pytest", str(path), "-s", "--tb=long", "--headed"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "PLAYBACK_SID": sid, "PYTHONUTF8": "1"},
        ),
    )
    stdout, stderr = await loop.run_in_executor(None, proc.communicate)
    finished_at = datetime.now(timezone.utc)
    raw_out = stdout.decode("utf-8", errors="replace")
    raw_err = stderr.decode("utf-8", errors="replace")

    # keep temp file for debugging
    # path.unlink(missing_ok=True)

    summary = {
        "id": sid,
        "case_name": case_name,
        "browser": browser,
        "status": "passed" if proc.returncode == 0 else "failed",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "rc": proc.returncode,
        "stdout": raw_out[-3000:],
        "stderr": raw_err[-500:],
    }

    screenshots = _find_screenshots(sid, raw_out, raw_err)
    if screenshots:
        summary["screenshot"] = screenshots[0]
    return summary


def _build_playwright_script(sid: str, name: str, steps: list[dict], browser: str) -> str:
    from app.services.script_gen import generate_script
    return generate_script(
        f"{name}_{sid}",
        steps,
        browser,
        breadcrumb=settings.breadcrumb_enabled,
        breadcrumb_id=name,
    )


def _find_screenshots(sid: str, stdout: str, stderr: str) -> list[str]:
    """Search for screenshot paths in output."""
    results = []
    import re
    for m in re.finditer(r'screenshot.*?(?:["\']([^"\']+\.png)["\']|screenshots/([^"\'\\s]+))', stdout + stderr, re.I):
        p = m.group(1) or m.group(2)
        if p:
            results.append(p)
    return results
