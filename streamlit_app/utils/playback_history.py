import json
import os
import time
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_HISTORY_FILE = os.path.join(_BASE_DIR, "logs", "playback_history.json")
_TMP_DIR = os.path.join(_BASE_DIR, "logs")


def _ensure_file():
    os.makedirs(os.path.dirname(_HISTORY_FILE), exist_ok=True)
    if not os.path.exists(_HISTORY_FILE):
        with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"records": []}, f, indent=2)


def load_all():
    _ensure_file()
    try:
        with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    return data.get("records", [])


def list_for_tc(tc_id, limit=5):
    records = [r for r in load_all() if r.get("tc_id") == tc_id]
    records.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return records[:limit]


def save_record(tc_id, status, duration_ms, browser, nav_timeout_ms=None, elem_timeout_ms=None, screenshot=None, exit_code=None, error=None):
    _ensure_file()
    record = {
        "tc_id": tc_id,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "duration_ms": int(duration_ms),
        "browser": browser,
        "nav_timeout_ms": nav_timeout_ms,
        "elem_timeout_ms": elem_timeout_ms,
        "screenshot": screenshot,
        "exit_code": exit_code,
        "error": error,
    }

    try:
        with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        data = {"records": []}

    data.setdefault("records", []).append(record)
    data["records"] = data["records"][-500:]

    tmp_path = _HISTORY_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, _HISTORY_FILE)

    cleanup_orphans(max_age_days=30)
    return record


def cleanup_orphans(max_age_days=30):
    cutoff = time.time() - max_age_days * 86400
    kept_screenshots = {r.get("screenshot") for r in load_all() if r.get("screenshot")}

    screenshots_dir = os.path.join(_BASE_DIR, "screenshots")
    if not os.path.isdir(screenshots_dir):
        return 0

    removed = 0
    for name in os.listdir(screenshots_dir):
        if not name.startswith("playback_"):
            continue
        full = os.path.join(screenshots_dir, name)
        rel = os.path.relpath(full, _BASE_DIR).replace(os.sep, "/")
        if rel in kept_screenshots:
            try:
                if os.path.getmtime(full) < cutoff:
                    os.remove(full)
                    removed += 1
            except OSError:
                pass
    return removed


def cleanup_stale_tmp_scripts(max_age_seconds=3600):
    if not os.path.isdir(_TMP_DIR):
        return 0
    cutoff = time.time() - max_age_seconds
    removed = 0
    for name in os.listdir(_TMP_DIR):
        if not (name.startswith("_playback_tmp_") and name.endswith(".py")):
            continue
        full = os.path.join(_TMP_DIR, name)
        try:
            if os.path.getmtime(full) < cutoff:
                os.remove(full)
                removed += 1
        except OSError:
            pass
    return removed


cleanup_stale_tmp_scripts()
