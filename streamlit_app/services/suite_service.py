"""套件业务层。

封装套件 CRUD、组合唯一校验、用例数统计。错误以 Exception 抛出，由 controller 捕获。
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from streamlit_app.utils import suite_store
from streamlit_app.utils.config_manager import get_current_user


class SuiteDuplicateError(Exception):
    """（name + version）组合重复。"""


def list_suites() -> List[Dict]:
    """列出全部套件，并附带动态统计的 case_count。"""
    suites = suite_store.load_all()
    testcases = _load_testcases()
    enriched: List[Dict] = []
    for s in suites:
        count = sum(1 for tc in testcases if tc.get("suite_id") == s["id"])
        enriched.append({**s, "case_count": count})
    enriched.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return enriched


def _load_testcases():
    from streamlit_app.utils.testcase_store import load_all
    return load_all()


def get_suite(suite_id: str) -> Optional[Dict]:
    return suite_store.get_by_id(suite_id)


def create_suite(name: str, version: str, created_by: Optional[str] = None) -> Dict:
    name = (name or "").strip()
    version = (version or "").strip()
    if not name:
        raise ValueError("系统名称不能为空")
    if not version:
        raise ValueError("版本号不能为空")

    if suite_store.find_by_name_version(name, version) is not None:
        raise SuiteDuplicateError(f"该系统名称 + 版本号的套件已存在：{name} / {version}")

    suite: Dict = {
        "id": str(uuid.uuid4()),
        "name": name,
        "version": version,
        "created_by": created_by or get_current_user(),
    }
    suite_store.save(suite)
    return suite_store.get_by_id(suite["id"]) or suite


def update_suite(suite_id: str, name: str, version: str) -> Optional[Dict]:
    name = (name or "").strip()
    version = (version or "").strip()
    if not name:
        raise ValueError("系统名称不能为空")
    if not version:
        raise ValueError("版本号不能为空")

    existing = suite_store.get_by_id(suite_id)
    if existing is None:
        return None

    dup = suite_store.find_by_name_version(name, version, exclude_id=suite_id)
    if dup is not None:
        raise SuiteDuplicateError(f"该系统名称 + 版本号的套件已存在：{name} / {version}")

    existing["name"] = name
    existing["version"] = version
    suite_store.save(existing)
    return suite_store.get_by_id(suite_id)


def delete_suite_if_empty(suite_id: str) -> Tuple[bool, str]:
    """空套件才能删。非空返回 (False, msg)。"""
    if suite_store.get_by_id(suite_id) is None:
        return False, "套件不存在"
    count = suite_store.count_testcases(suite_id)
    if count > 0:
        return False, f"套件内还有 {count} 条用例，请先删除"
    suite_store.delete(suite_id)
    return True, ""
