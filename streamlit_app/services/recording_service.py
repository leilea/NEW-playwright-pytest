import os
import re
import subprocess
import tempfile
import threading
import time
import uuid


ACTION_MAP = {
    "goto": "navigate",
    "click": "click",
    "fill": "fill",
    "type": "fill",
    "press": "fill",
    "dblclick": "click",
    "check": "check",
    "uncheck": "uncheck",
    "select_option": "select",
    "hover": "hover",
    "clear": "clear",
    "scroll_into_view_if_needed": "scroll",
}

ACTION_DESC_MAP = {
    "navigate": "页面导航",
    "click": "点击元素",
    "fill": "输入文本",
    "verify": "断言验证",
    "hover": "悬停元素",
    "scroll": "滚动到元素",
    "clear": "清空输入",
    "select": "选择选项",
    "check": "勾选",
    "uncheck": "取消勾选",
}


def _extract_selector(expr):
    if not expr:
        return ""
    expr = expr.strip()
    if expr.startswith("'") or expr.startswith('"'):
        return expr.strip("'\"")
    if re.match(r"^page\.(get_by_|locator\()", expr):
        return expr
    return expr


def _extract_value(expr):
    if not expr:
        return ""
    expr = expr.strip()
    if expr.startswith("'") or expr.startswith('"'):
        return expr.strip("'\"")
    return expr


def _parse_script_to_steps(script_text):
    steps = []
    lines = script_text.strip().split("\n")

    line_patterns = [
        (r"\.goto\((.+?)\)", "goto"),
        (r"\.click\((.+?)\)", "click"),
        (r"\.dblclick\((.+?)\)", "dblclick"),
        (r"\.fill\((.+?),\s*(.+?)\)", "fill"),
        (r"\.type\((.+?),\s*(.+?)\)", "type"),
        (r"\.press\((.+?),\s*(.+?)\)", "press"),
        (r"\.clear\((.+?)\)", "clear"),
        (r"\.check\((.+?)\)", "check"),
        (r"\.uncheck\((.+?)\)", "uncheck"),
        (r"\.hover\((.+?)\)", "hover"),
        (r"\.select_option\((.+?),\s*(.+?)\)", "select_option"),
        (r"\.scroll_into_view_if_needed\((.+?)\)", "scroll_into_view_if_needed"),
        (r"\.toBeVisible\(\)", "verify"),
    ]

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        matched = False
        for pattern, action_key in line_patterns:
            m = re.search(pattern, line)
            if m:
                selector = _extract_selector(m.group(1)) if m.lastindex and m.lastindex >= 1 else ""
                value = ""
                if action_key == "fill" and m.lastindex and m.lastindex >= 2:
                    value = _extract_value(m.group(2))
                elif action_key == "type" and m.lastindex and m.lastindex >= 2:
                    value = _extract_value(m.group(2))
                elif action_key == "press" and m.lastindex and m.lastindex >= 2:
                    value = _extract_value(m.group(2))
                elif action_key == "select_option" and m.lastindex and m.lastindex >= 2:
                    value = _extract_value(m.group(2))

                action = ACTION_MAP.get(action_key, action_key)

                step = {
                    "id": str(uuid.uuid4()),
                    "action": action,
                    "selector": selector,
                    "value": value,
                    "description": ACTION_DESC_MAP.get(action, "步骤"),
                }
                steps.append(step)
                matched = True
                break

        if not matched and "expect" in line and "toBeVisible" in line:
            m = re.search(r"expect\((.+?)\)", line)
            selector = ""
            if m:
                selector = m.group(1).strip()
            steps.append({
                "id": str(uuid.uuid4()),
                "action": "verify",
                "selector": selector,
                "value": "",
                "description": "断言可见",
            })
            matched = True

        if not matched and line:
            steps.append({
                "id": str(uuid.uuid4()),
                "action": "unknown",
                "selector": line,
                "value": "",
                "description": "未知操作",
            })

    return steps


def start_recording(env="qa"):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    target_url = os.environ.get("RECORDING_URL", "")
    if not target_url:
        config_path = os.path.join(base_dir, "config", "test_config.py")
        if os.path.exists(config_path):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("test_config", config_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                target_url = os.environ.get("RECORDING_URL", "")
                if not target_url:
                    cfg = mod.TestConfig()
                    target_url = cfg.base_url
            except Exception:
                pass
    if not target_url:
        target_url = "https://demoqa.com"

    tmpfile = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
    tmpfile.write("")
    tmpfile.close()

    cmd = ["playwright", "codegen", "--target", "python", "--output", tmpfile.name,
           "--viewport-size", "1280,720", target_url]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=base_dir,
        bufsize=1,
    )

    result = {"script": "", "tmpfile": tmpfile.name, "proc": proc, "error": None, "target_url": target_url, "__rs_source": __file__, "__rs_v": 1}

    def _wait():
        try:
            proc.wait()
            time.sleep(0.5)
            try:
                with open(tmpfile.name, "r", encoding="utf-8") as f:
                    script = f.read()
                script = _inject_initial_navigation(script, target_url)
                result["script"] = script
            except Exception as e:
                result["error"] = str(e)
        except Exception as e:
            result["error"] = str(e)

    thread = threading.Thread(target=_wait, daemon=True)
    thread.start()
    result["thread"] = thread

    return result


def get_recording_result(rec_result):
    if rec_result["thread"].is_alive():
        return {"status": "recording", "script": "", "steps": []}

    rec_result["thread"].join(timeout=5)

    if rec_result["error"]:
        return {"status": "error", "script": "", "steps": [], "error": rec_result["error"]}

    script = rec_result.get("script", "")
    steps = _parse_script_to_steps(script)

    stats = _compute_stats(steps)

    return {"status": "done", "script": script, "steps": steps, "stats": stats}


def stop_recording(rec_result):
    proc = rec_result.get("proc")
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _inject_initial_navigation(script: str, target_url: str) -> str:
    script, _ = re.subn(
        r'page\.goto\(["\']about:blank["\']\)',
        f'page.goto("{target_url}")',
        script, count=1,
    )
    if "page.goto(" not in script:
        lines = script.split("\n")
        out = []
        for line in lines:
            out.append(line)
            if re.search(r"\.new_page\(", line):
                indent = re.match(r"^(\s*)", line).group(1)
                out.append(f'{indent}page.goto("{target_url}")')
        script = "\n".join(out)
    return script


def _compute_stats(steps):
    total = len(steps)
    navigates = sum(1 for s in steps if s["action"] == "navigate")
    clicks = sum(1 for s in steps if s["action"] == "click")
    fills = sum(1 for s in steps if s["action"] == "fill")
    verifies = sum(1 for s in steps if s["action"] == "verify")
    others = total - navigates - clicks - fills - verifies
    return {
        "total": total,
        "navigate": navigates,
        "click": clicks,
        "fill": fills,
        "verify": verifies,
        "other": others,
    }