import os
import re
import sys
import queue
import subprocess
import threading
import time
import uuid
from typing import Generator

from streamlit_app.utils import playback_history

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASE_DIR, "logs")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
TMP_DIR = LOG_DIR

NAV_TIMEOUT_MS = 30_000
ELEM_TIMEOUT_MS = 10_000
MAX_TIMEOUT_S = 300
NAV_MIN_MS = 5_000
NAV_MAX_MS = 120_000
ELEM_MIN_MS = 1_000
ELEM_MAX_MS = 30_000
POLL_TIMEOUT_S = 0.1

VALID_BROWSERS = ("chromium", "firefox", "webkit")

_HAS_SYNCHRONOUS_PLAYWRIGHT = re.compile(r"^\s*from\s+playwright\.sync_api\s+import", re.M)
_HAS_PLAYWRIGHT_IMPORT = re.compile(r"^\s*(?:import|from)\+splaywright", re.M)
_HAS_PAGE_ASSIGNMENT = re.compile(r"^\s*page\s*=", re.M)
_HAS_RUN_FUNCTION = re.compile(r"^\s*def\s+run\s*\(", re.M)
_HAS_WITH_SYNC = re.compile(r"^\s*with\s+sync_playwright\s*\(\s*\)", re.M)
_GOTO_RE = re.compile(r"^\s*page\.goto\(")
_PAGE_CREATION_RE = re.compile(r"^(\s*page\s*=\s*(?:context|browser)\.new_page\(\))\s*$", re.MULTILINE)
_LOCATOR_ACTIONS = frozenset({"click", "fill", "check", "uncheck", "select_option", "dblclick", "hover", "clear", "press"})

_PLAYBACK_PRELUDE = '''\
import sys, traceback, time, os
from playwright.sync_api import sync_playwright

__PLAYBACK_GLOBALS__ = {"__name__": "__main__"}
err_screenshot = None
_exit_code = 0
try:
    exec(compile(__USER_SCRIPT_SRC__, "<playback_user>", "exec"), __PLAYBACK_GLOBALS__)
    print("[PLAYBACK] OK")
except SystemExit as _se:
    _exit_code = _se.code if isinstance(_se.code, int) else (0 if _se.code is None else 1)
    if _exit_code != 0:
        traceback.print_exc()
        try:
            _page_obj = __PLAYBACK_GLOBALS__.get("_PLAYBACK_PAGE")
            if _page_obj:
                _ts = int(time.time())
                _err_path = f"screenshots/playback_err_{_ts}.png"
                os.makedirs("screenshots", exist_ok=True)
                _page_obj.screenshot(path=_err_path)
                err_screenshot = _err_path
        except Exception:
            pass
        print(f"[PLAYBACK] FAILED;SCREENSHOT={{err_screenshot or 'none'}}")
except Exception as _e:
    traceback.print_exc()
    try:
        _page_obj = __PLAYBACK_GLOBALS__.get("_PLAYBACK_PAGE")
        if _page_obj:
            _ts = int(time.time())
            _err_path = f"screenshots/playback_err_{_ts}.png"
            os.makedirs("screenshots", exist_ok=True)
            _page_obj.screenshot(path=_err_path)
            err_screenshot = _err_path
    except Exception:
        pass
    print(f"[PLAYBACK] FAILED;SCREENSHOT={{err_screenshot or 'none'}}")
    _exit_code = 1

sys.exit(_exit_code)
'''


def _is_full_module(script: str) -> bool:
    return bool(
        _HAS_SYNCHRONOUS_PLAYWRIGHT.search(script)
        and _HAS_RUN_FUNCTION.search(script)
        and _HAS_WITH_SYNC.search(script)
    )


def _has_page_assignment(script: str) -> bool:
    return bool(_HAS_PAGE_ASSIGNMENT.search(script))


def _has_playwright_import(script: str) -> bool:
    return bool(_HAS_SYNCHRONOUS_PLAYWRIGHT.search(script) or _HAS_PLAYWRIGHT_IMPORT.search(script))


def _inject_timeout_setters(script: str, nav_timeout_ms: int, elem_timeout_ms: int) -> str:
    """Inject page.set_default_timeout / set_default_navigation_timeout
    and a global page reference right after page = context/browser.new_page()."""
    def _replacer(m):
        line = m.group(1)
        indent = re.match(r"^(\s*)", line).group(1)
        return (f'{line}\n'
                f'{indent}page.set_default_timeout({int(elem_timeout_ms)})\n'
                f'{indent}page.set_default_navigation_timeout({int(nav_timeout_ms)})\n'
                f'{indent}global _PLAYBACK_PAGE\n'
                f'{indent}_PLAYBACK_PAGE = page')
    return _PAGE_CREATION_RE.sub(_replacer, script)


def _inject_navigation_strategy(script: str, nav_timeout_ms: int) -> str:
    """Replace page.goto(url) with:
    page.goto(url, wait_until="domcontentloaded", timeout=N)
    page.wait_for_load_state("networkidle", timeout=N)
    """
    lines = script.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if _GOTO_RE.match(stripped) and "wait_until" not in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            paren_start = stripped.index("(")
            depth = 0
            end = paren_start
            for i, ch in enumerate(stripped[paren_start:], start=paren_start):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            inner = stripped[paren_start + 1:end]
            result.append(f'{indent}page.goto({inner}, wait_until="domcontentloaded", timeout={int(nav_timeout_ms)})')
            result.append(f'{indent}page.wait_for_load_state("networkidle", timeout={int(nav_timeout_ms)})')
        else:
            result.append(line)
    return "\n".join(result)


def _inject_explicit_waits(script: str, elem_timeout_ms: int) -> str:
    """Inject locator.wait_for(timeout=N) before each locator action (click, fill, ...)."""
    lines = script.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("page.") and stripped.rstrip().endswith(")"):
            best_pos = -1
            best_action = None
            for action in _LOCATOR_ACTIONS:
                marker = f".{action}("
                pos = stripped.rfind(marker)
                if pos > best_pos:
                    best_pos = pos
                    best_action = action
            if best_pos >= 0 and best_action:
                locator_part = stripped[:best_pos]
                indent = line[:len(line) - len(line.lstrip())]
                result.append(f'{indent}{locator_part}.wait_for(timeout={int(elem_timeout_ms)})')
        result.append(line)
    return "\n".join(result)


def _wrap_full_module(script: str, nav_timeout_ms: int, elem_timeout_ms: int) -> str:
    enhanced = _inject_timeout_setters(script, nav_timeout_ms, elem_timeout_ms)
    enhanced = _inject_navigation_strategy(enhanced, nav_timeout_ms)
    enhanced = _inject_explicit_waits(enhanced, elem_timeout_ms)
    user_literal = repr(enhanced)
    return _PLAYBACK_PRELUDE.replace("__USER_SCRIPT_SRC__", user_literal)


def _wrap_partial_script(script: str, browser: str, headless: bool, nav_timeout_ms: int, elem_timeout_ms: int) -> str:
    enhanced = _inject_navigation_strategy(script, nav_timeout_ms)
    enhanced = _inject_explicit_waits(enhanced, elem_timeout_ms)
    indented = "\n".join(("        " + line) if line.strip() else line for line in enhanced.splitlines())
    body = (
        "import sys, traceback, time, os\n"
        "from playwright.sync_api import sync_playwright\n"
        "_PLAYBACK_PAGE = None\n"
        "err_screenshot = None\n"
        "_exit_code = 0\n"
        "try:\n"
        "    with sync_playwright() as p:\n"
        f"        browser = p.{browser}.launch(headless={headless})\n"
        "        context = browser.new_context()\n"
        "        page = context.new_page()\n"
        f"        page.set_default_timeout({int(elem_timeout_ms)})\n"
        f"        page.set_default_navigation_timeout({int(nav_timeout_ms)})\n"
        "        _PLAYBACK_PAGE = page\n"
        "        # === USER SCRIPT BELOW ===\n"
        f"{indented}\n"
        "        # === USER SCRIPT ABOVE ===\n"
        "        context.close()\n"
        "        browser.close()\n"
        "        print('[PLAYBACK] OK')\n"
        "except SystemExit as _se:\n"
        "    raise\n"
        "except Exception as _e:\n"
        "    traceback.print_exc()\n"
        "    try:\n"
        "        if _PLAYBACK_PAGE:\n"
        "            ts = int(time.time())\n"
        "            err_path = f'screenshots/playback_err_{ts}.png'\n"
        "            os.makedirs('screenshots', exist_ok=True)\n"
        "            _PLAYBACK_PAGE.screenshot(path=err_path)\n"
        "            err_screenshot = err_path\n"
        "    except Exception:\n"
        "        pass\n"
        "    print(f'[PLAYBACK] FAILED;SCREENSHOT={err_screenshot or \"none\"}')\n"
        "    _exit_code = 1\n"
        "sys.exit(_exit_code)\n"
    )
    return body


def _wrap_script(script_text: str, browser: str, headless: bool, nav_timeout_ms: int, elem_timeout_ms: int) -> str:
    if not script_text or not script_text.strip():
        raise ValueError("用例脚本为空，无法回放")

    if _is_full_module(script_text):
        return _wrap_full_module(script_text, nav_timeout_ms, elem_timeout_ms)
    if _has_page_assignment(script_text) and _has_playwright_import(script_text):
        return _wrap_full_module(script_text, nav_timeout_ms, elem_timeout_ms)
    return _wrap_partial_script(script_text, browser, headless, nav_timeout_ms, elem_timeout_ms)


def _validate_wrapped_syntax(wrapped: str) -> tuple[bool, str | None]:
    try:
        compile(wrapped, "<playback>", "exec")
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} (line {e.lineno})"


def _parse_screenshot_marker(output_lines: list[str]) -> str | None:
    pattern = re.compile(r"\[PLAYBACK\]\s+FAILED;SCREENSHOT=(\S+)")
    for line in output_lines:
        m = pattern.search(line)
        if m:
            val = m.group(1)
            if val and val != "none":
                return val
    return None


def _resolve_screenshot_path(screenshot: str | None) -> str | None:
    if not screenshot:
        return None
    if os.path.isabs(screenshot):
        return screenshot if os.path.exists(screenshot) else None
    candidate = os.path.join(BASE_DIR, screenshot)
    return candidate if os.path.exists(candidate) else None


def _cleanup_tmp(path: str | None) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _terminate(proc: subprocess.Popen) -> None:
    try:
        proc.terminate()
    except Exception:
        pass
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass


def playback_stream(
    tc: dict,
    browser: str = "chromium",
    headless: bool = True,
    nav_timeout_ms: int = NAV_TIMEOUT_MS,
    elem_timeout_ms: int = ELEM_TIMEOUT_MS,
) -> Generator[str, None, dict]:
    tc_id = tc.get("id", "unknown")
    script_text = tc.get("script", "")
    browser = browser if browser in VALID_BROWSERS else "chromium"
    nav_timeout_ms = max(NAV_MIN_MS, min(NAV_MAX_MS, int(nav_timeout_ms)))
    elem_timeout_ms = max(ELEM_MIN_MS, min(ELEM_MAX_MS, int(elem_timeout_ms)))

    started = time.time()

    try:
        wrapped = _wrap_script(script_text, browser, headless, nav_timeout_ms, elem_timeout_ms)
    except ValueError as e:
        result = {
            "status": "error",
            "duration_ms": int((time.time() - started) * 1000),
            "exit_code": None,
            "browser": browser,
            "screenshot": None,
            "error": str(e),
        }
        playback_history.save_record(tc_id=tc_id, **result)
        yield f"[PLAYBACK] ERROR: {e}\n"
        return result

    ok, syntax_err = _validate_wrapped_syntax(wrapped)
    if not ok:
        result = {
            "status": "error",
            "duration_ms": int((time.time() - started) * 1000),
            "exit_code": None,
            "browser": browser,
            "screenshot": None,
            "error": syntax_err,
        }
        playback_history.save_record(tc_id=tc_id, **result)
        yield f"[PLAYBACK] {syntax_err}\n"
        return result

    os.makedirs(TMP_DIR, exist_ok=True)
    tmp_name = f"_playback_tmp_{uuid.uuid4().hex}.py"
    tmp_path = os.path.join(TMP_DIR, tmp_name)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(wrapped)

    log_name = f"playback_{tc_id}_{int(started)}.log"
    log_path = os.path.join(LOG_DIR, log_name)

    yield f"[PLAYBACK] ▶ 启动子进程 (browser={browser}, headless={headless}, nav_timeout={nav_timeout_ms}ms, elem_timeout={elem_timeout_ms}ms)\n"
    yield f"[PLAYBACK] tmp script: {os.path.relpath(tmp_path, BASE_DIR)}\n"

    env_dict = {**os.environ, "PYTHONPATH": BASE_DIR, "PYTHONUNBUFFERED": "1"}

    try:
        proc = subprocess.Popen(
            [sys.executable, "-u", tmp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env_dict,
            cwd=BASE_DIR,
        )
    except OSError as e:
        _cleanup_tmp(tmp_path)
        result = {
            "status": "error",
            "duration_ms": int((time.time() - started) * 1000),
            "exit_code": None,
            "browser": browser,
            "screenshot": None,
            "error": f"启动子进程失败: {e}",
        }
        playback_history.save_record(tc_id=tc_id, **result)
        yield f"[PLAYBACK] ERROR: {e}\n"
        return result

    handle = {"proc": proc, "tmp": tmp_path, "log": log_path}
    output_queue: queue.Queue = queue.Queue()
    completed = threading.Event()
    captured_lines: list[str] = []

    def _reader():
        try:
            with open(log_path, "w", encoding="utf-8") as lf:
                for line in iter(proc.stdout.readline, ""):
                    output_queue.put(line)
                    captured_lines.append(line)
                    lf.write(line)
                    lf.flush()
        except Exception:
            pass
        finally:
            try:
                if proc.stdout:
                    proc.stdout.close()
            except Exception:
                pass
            completed.set()

    reader_thread = threading.Thread(target=_reader, daemon=True)
    reader_thread.start()

    timed_out = False
    deadline = started + MAX_TIMEOUT_S
    while True:
        try:
            line = output_queue.get(timeout=POLL_TIMEOUT_S)
            yield line
        except queue.Empty:
            if time.time() > deadline:
                timed_out = True
                _terminate(proc)
                yield f"\n[PLAYBACK] ⏱️ 超时（>{MAX_TIMEOUT_S}s），已强制终止\n"
                break
            if completed.is_set() and output_queue.empty():
                break

    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _terminate(proc)
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass

    duration_ms = int((time.time() - started) * 1000)
    exit_code = proc.returncode
    screenshot = _resolve_screenshot_path(_parse_screenshot_marker(captured_lines))

    if timed_out:
        status = "error"
        error = f"timeout:>{MAX_TIMEOUT_S}s"
    elif exit_code == 0:
        status = "passed"
        error = None
    else:
        status = "failed"
        error = f"exit_code={exit_code}"

    result = {
        "status": status,
        "duration_ms": duration_ms,
        "exit_code": exit_code,
        "browser": browser,
        "nav_timeout_ms": nav_timeout_ms,
        "elem_timeout_ms": elem_timeout_ms,
        "screenshot": screenshot,
        "error": error,
    }
    playback_history.save_record(tc_id=tc_id, **result)
    yield f"[PLAYBACK] 完成: status={status}, duration={duration_ms}ms, exit={exit_code}\n"
    if screenshot:
        yield f"[PLAYBACK] 截图: {os.path.relpath(screenshot, BASE_DIR)}\n"

    _cleanup_tmp(tmp_path)
    return result


def stop_playback(handle: dict) -> None:
    proc = handle.get("proc")
    if proc is None:
        return
    _terminate(proc)
    _cleanup_tmp(handle.get("tmp"))
