"""PlaybackService — run a recorded test case via Playwright subprocess."""
import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings


async def run_playback(case_name: str, steps: list[dict], browser: str, ws_token: str) -> dict:
    """Execute steps via playwright subprocess. Returns summary dict."""
    sid = uuid.uuid4().hex[:8]
    script = _build_playwright_script(sid, case_name, steps, browser)
    path = Path(settings.log_dir) / f"playback_{sid}.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script, encoding="utf-8")

    started_at = datetime.now(timezone.utc)
    proc = await asyncio.create_subprocess_exec(
        "python", str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, "PLAYBACK_SID": sid},
    )
    stdout, stderr = await proc.communicate()
    finished_at = datetime.now(timezone.utc)
    raw_out = stdout.decode(errors="replace")
    raw_err = stderr.decode(errors="replace")

    path.unlink(missing_ok=True)

    summary = {
        "id": sid,
        "case_name": case_name,
        "browser": browser,
        "status": "passed" if proc.returncode == 0 else "failed",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "rc": proc.returncode,
        "stdout": raw_out[-2000:],
        "stderr": raw_err[-500:],
    }

    screenshots = _find_screenshots(sid, raw_out, raw_err)
    if screenshots:
        summary["screenshot"] = screenshots[0]
    return summary


def _build_playwright_script(sid: str, name: str, steps: list[dict], browser: str) -> str:
    from app.services.script_gen import generate_script
    return generate_script(f"{name}_{sid}", steps, browser)


def _find_screenshots(sid: str, stdout: str, stderr: str) -> list[str]:
    """Search for screenshot paths in output."""
    results = []
    import re
    for m in re.finditer(r'screenshot.*?(?:["\']([^"\']+\.png)["\']|screenshots/([^"\'\\s]+))', stdout + stderr, re.I):
        p = m.group(1) or m.group(2)
        if p:
            results.append(p)
    return results
