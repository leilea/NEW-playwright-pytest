"""PlaybackService — run a recorded test case via Playwright subprocess."""
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

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

    if summary["status"] != "passed":
        summary["error_info"] = _parse_playback_error(raw_out, raw_err, steps)

    return summary


def _build_playwright_script(sid: str, name: str, steps: list[dict], browser: str) -> str:
    from app.services.script_gen import generate_script
    return generate_script(
        f"{name}_{sid}",
        steps,
        browser,
    )


def _find_screenshots(sid: str, stdout: str, stderr: str) -> list[str]:
    """Search for screenshot paths in output."""
    results = []
    for m in re.finditer(r'screenshot.*?(?:["\']([^"\']+\.png)["\']|screenshots/([^"\'\\s]+))', stdout + stderr, re.I):
        p = m.group(1) or m.group(2)
        if p:
            results.append(p)
    return results


def _parse_playback_error(stdout: str, stderr: str, steps: list[dict] | None = None) -> dict | None:
    """Parse structured error info from pytest/Playwright output.

    Returns None when no recognized error pattern is found.
    """
    text = stderr + "\n" + stdout

    # 1. locator timeout: Locator.click: Timeout 30000ms exceeded.
    m = re.search(r'Locator\.(\w+):.*Timeout (\d+)ms exceeded', text)
    if m:
        timeout_ms = int(m.group(2))
        step_index, step_action, step_selector = _find_step_by_marker(stdout, text, m.start(), steps)
        locator = step_selector or _extract_locator_from_context(text, m.start())
        result = {
            "type": "timeout",
            "locator": locator or "未知定位器",
            "detail": _timeout_detail(timeout_ms, locator, step_index, step_action),
            "timeout_ms": timeout_ms,
        }
        if step_index is not None:
            result["step_index"] = step_index
        return result

    # 2. strict mode violation: locator("//xpath") resolved to 2 elements
    m = re.search(r'strict mode violation: locator\((.+?)\) resolved to (\d+) elements', text)
    if m:
        locator = m.group(1)
        elements = _extract_matching_elements(text, m.end())
        return {
            "type": "strict_violation",
            "locator": locator,
            "detail": "定位器匹配到多个元素，无法确定操作目标",
            "elements": elements,
        }

    # 3. wait_for_load_state timeout
    m = re.search(r'wait_for_load_state.*Timeout (\d+)ms exceeded', text, re.DOTALL)
    if m:
        timeout_ms = int(m.group(1))
        state_m = re.search(r"""wait_for_load_state\('?"?(\w+)'?"?""", text)
        state = state_m.group(1) if state_m else "networkidle"
        return {
            "type": "load_state_timeout",
            "locator": "",
            "detail": f"页面加载状态超时（{state}），页面请求未完成",
            "timeout_ms": timeout_ms,
        }

    # 4. assertion failure
    if re.search(r'AssertionError|to_be_visible|to_be_hidden|to_be_enabled|to_be_disabled|to_be_editable|to_contain_text', text):
        m = re.search(r'expect\((.+?)\)\.to_(.+?)\(\)', text, re.DOTALL)
        locator = m.group(1) if m else ""
        state = m.group(2) if m else "visible"
        return {
            "type": "assertion",
            "locator": locator,
            "detail": f"元素状态断言失败，期望状态: {state}",
            "expected_state": state,
        }

    m = re.search(r'<(\S[^>]*?)>.*?intercepts pointer events', text)
    if m:
        overlay_tag = m.group(1)
        locator = _extract_locator_from_context(text, m.start())
        return {
            "type": "overlay_intercepted",
            "locator": locator or "未知定位器",
            "detail": _overlay_detail(overlay_tag, locator),
            "overlay_element": overlay_tag,
        }

    return None


def _find_step_by_marker(stdout: str, text: str, error_pos: int, steps: list[dict] | None) -> tuple[int | None, str, str]:
    """Search stdout for the last __STEP_MARKER__:N before error_pos.

    Returns (step_index, action, selector) from the steps list, or
    (None, '', '') when no marker is found or steps are not provided.
    """
    if not steps:
        return None, "", ""

    markers = list(re.finditer(r'__STEP_MARKER__:(\d+)', stdout))
    if not markers:
        return None, "", ""

    best = None
    for m in reversed(markers):
        marker_end = m.end()
        marker_abs = text.find(m.group(0))
        if marker_abs == -1:
            marker_abs = marker_end
        if marker_abs < error_pos:
            best = m
            break

    if best is None:
        return None, "", ""

    idx = int(best.group(1))
    if idx < len(steps):
        step = steps[idx]
        action = step.get("action", "")
        params = dict(step.get("params") or step)
        selector = params.get("selector", "")
        return idx, action, selector

    return None, "", ""


def _extract_locator_from_context(text: str, pos: int) -> str:
    """Search backward from pos to find the failing locator expression."""
    before = text[max(0, pos - 800):pos]
    m = re.search(r'(?:locator|get_by_text|get_by_role|get_by_label|get_by_placeholder|get_by_test_id|get_by_alt_text|get_by_title)\(([^)]+)\)', before)
    if m:
        return m.group(1)
    m = re.search(r'_safe\(page,\s*\[([^\]]+)\]', before)
    if m:
        strategies = [s.strip().strip('"').strip("'") for s in m.group(1).split(",") if s.strip()]
        return " | ".join(s[:50] for s in strategies[:3])
    return ""


def _extract_matching_elements(text: str, start: int) -> list[str]:
    """Extract the HTML snippets of matching elements after strict violation."""
    after = text[start:start + 500]
    return re.findall(r'\d+\)\s*<(.+?)>', after)[:10]


def _timeout_detail(timeout_ms: int, locator: str, step_index: int | None = None, action: str = "") -> str:
    loc = f"，定位器：{locator}" if locator and locator != "未知定位器" else ""
    prefix = f"第 {step_index + 1} 步 [{action}] " if step_index is not None else ""
    return f"{prefix}定位元素超时，等待 {timeout_ms}ms 后仍未找到{loc}"


def _overlay_detail(overlay_tag: str, locator: str) -> str:
    loc = f"，目标元素定位器：{locator}" if locator and locator != "未知定位器" else ""
    return f"元素被弹窗遮罩 <{overlay_tag}> 遮挡，请检查弹窗是否关闭{loc}"
