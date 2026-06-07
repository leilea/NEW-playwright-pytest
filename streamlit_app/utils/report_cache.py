import json
import os
from datetime import datetime

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "trends.json")


def _ensure_cache():
    if not os.path.exists(CACHE_FILE):
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump({"runs": []}, f)


def save_run(summary, env, browser, markers):
    _ensure_cache()
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    data["runs"].append({
        "timestamp": datetime.now().isoformat(),
        "total": summary["total"],
        "passed": summary["passed"],
        "failed": summary["failed"],
        "skipped": summary["skipped"],
        "broken": summary["broken"],
        "pass_rate": summary["pass_rate"],
        "env": env,
        "browser": browser,
        "markers": markers,
    })
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_trends():
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    return data.get("runs", [])
