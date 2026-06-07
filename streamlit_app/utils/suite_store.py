"""套件持久化层（JSON 文件 + 临时文件原子写）。

仿 `testcase_store.py` 风格：薄薄一层、纯文件、无锁。
"""
import json
import os
from datetime import datetime
from typing import List, Optional

STORE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "suites.json")


def _ensure_store():
    if not os.path.exists(STORE_FILE):
        os.makedirs(os.path.dirname(STORE_FILE), exist_ok=True)
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"suites": []}, f, ensure_ascii=False)


def _atomic_write(data: dict) -> None:
    """写回 JSON：先写临时文件再 os.replace 原子替换。"""
    tmp = STORE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STORE_FILE)


def load_all() -> List[dict]:
    _ensure_store()
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("suites", [])


def get_by_id(suite_id: str) -> Optional[dict]:
    suites = load_all()
    for s in suites:
        if s["id"] == suite_id:
            return s
    return None


def save(suite: dict) -> None:
    """新增或更新一条套件记录。写入时刷新 updated_at。"""
    _ensure_store()
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    suites = data.get("suites", [])

    now = datetime.now().isoformat()
    suite["updated_at"] = now

    for i, s in enumerate(suites):
        if s["id"] == suite["id"]:
            suites[i] = suite
            break
    else:
        suite["created_at"] = now
        suites.append(suite)

    data["suites"] = suites
    _atomic_write(data)


def delete(suite_id: str) -> None:
    _ensure_store()
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["suites"] = [s for s in data.get("suites", []) if s["id"] != suite_id]
    _atomic_write(data)


def count_testcases(suite_id: str, testcases: Optional[List[dict]] = None) -> int:
    """统计某套件下的用例数。

    为避免循环依赖，未直接 import testcase_store；调用方可传入已加载的 testcases 列表。
    """
    if testcases is None:
        from streamlit_app.utils.testcase_store import load_all as _load_testcases
        testcases = _load_testcases()
    return sum(1 for tc in testcases if tc.get("suite_id") == suite_id)


def find_by_name_version(name: str, version: str, exclude_id: Optional[str] = None) -> Optional[dict]:
    """按 (name, version) 查重；exclude_id 用于更新时排除自己。"""
    for s in load_all():
        if s.get("name") == name and s.get("version") == version:
            if exclude_id is not None and s.get("id") == exclude_id:
                continue
            return s
    return None
