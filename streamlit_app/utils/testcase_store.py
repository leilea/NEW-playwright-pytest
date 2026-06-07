import json
import os
import uuid
from datetime import datetime
from typing import List, Optional

STORE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "testcases.json")


def _ensure_store():
    if not os.path.exists(STORE_FILE):
        os.makedirs(os.path.dirname(STORE_FILE), exist_ok=True)
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"testcases": []}, f, ensure_ascii=False)


def _atomic_write(data: dict) -> None:
    """写回 JSON：先写临时文件再 os.replace 原子替换。"""
    tmp = STORE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STORE_FILE)


def load_all() -> List[dict]:
    _ensure_store()
    _migrate_default_suite()
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("testcases", [])


def get_by_id(tc_id):
    testcases = load_all()
    for tc in testcases:
        if tc["id"] == tc_id:
            return tc
    return None


def save(testcase: dict, suite_id: Optional[str] = None) -> None:
    """新增 / 更新一条用例。suite_id 仅在新增时使用；兼容历史无 suite_id 数据。"""
    _ensure_store()
    if suite_id is not None:
        testcase["suite_id"] = suite_id
    if "suite_id" not in testcase or not testcase.get("suite_id"):
        import warnings
        warnings.warn(
            f"save() called without suite_id for testcase id={testcase.get('id', '<new>')}; "
            "data persisted without suite ownership",
            stacklevel=2,
        )
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    testcases = data.get("testcases", [])

    now = datetime.now().isoformat()
    testcase["updated_at"] = now

    for i, tc in enumerate(testcases):
        if tc["id"] == testcase["id"]:
            testcases[i] = testcase
            break
    else:
        testcase["created_at"] = now
        testcases.append(testcase)

    data["testcases"] = testcases
    _atomic_write(data)


def delete(tc_id):
    _ensure_store()
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["testcases"] = [tc for tc in data.get("testcases", []) if tc["id"] != tc_id]
    _atomic_write(data)


def _migrate_default_suite() -> None:
    """启动期幂等迁移：把无 suite_id 的历史用例归入「默认系统 / v1.0」。

    流程：
    1. 加载所有用例；无孤儿直接 return
    2. 加载所有套件；若无「默认系统」则创建一个（uuid4 / v1.0 / current_user）
    3. 把所有孤儿用例的 suite_id 写为该套件 id，原子写回

    该函数只读取 / 写入本文件，不依赖 suite_store.py 的 _ensure_store（避免循环），
    但复用 suite_store 提供的 _atomic_write 风格 + 直接构造 suite dict。
    """
    if not os.path.exists(STORE_FILE):
        return

    try:
        with open(STORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return

    testcases = data.get("testcases", [])
    orphans = [tc for tc in testcases if not tc.get("suite_id")]
    if not orphans:
        return

    suite_store_file = os.path.join(os.path.dirname(STORE_FILE), "suites.json")
    suites_data: dict = {"suites": []}
    if os.path.exists(suite_store_file):
        try:
            with open(suite_store_file, "r", encoding="utf-8") as f:
                suites_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            suites_data = {"suites": []}

    default_suite = None
    for s in suites_data.get("suites", []):
        if s.get("name") == "默认系统":
            default_suite = s
            break

    if default_suite is None:
        from streamlit_app.utils.config_manager import get_current_user
        now = datetime.now().isoformat()
        default_suite = {
            "id": str(uuid.uuid4()),
            "name": "默认系统",
            "version": "v1.0",
            "created_by": get_current_user(),
            "created_at": now,
            "updated_at": now,
        }
        suites_data.setdefault("suites", []).append(default_suite)
        os.makedirs(os.path.dirname(suite_store_file), exist_ok=True)
        tmp = suite_store_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(suites_data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, suite_store_file)

    default_id = default_suite["id"]
    for tc in testcases:
        if not tc.get("suite_id"):
            tc["suite_id"] = default_id

    data["testcases"] = testcases
    _atomic_write(data)
