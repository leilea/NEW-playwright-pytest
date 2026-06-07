import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from streamlit_app.utils import testcase_store, suite_store
from streamlit_app.utils.testcase_store import load_all, get_by_id, save, delete


PRIORITY_MAP: Dict[str, str] = {"P0": "🔴 P0", "P1": "🟡 P1", "P2": "🟢 P2"}
PRIORITY_OPTIONS: List[str] = ["P0", "P1", "P2"]
ACTION_OPTIONS: List[str] = [
    "navigate", "click", "dblclick", "fill", "hover", "clear",
    "scroll", "select", "check", "uncheck", "verify",
]
ACTION_DESC_MAP: Dict[str, str] = {
    "navigate": "页面导航",
    "click": "点击元素",
    "dblclick": "双击元素",
    "fill": "输入文本",
    "hover": "悬停元素",
    "clear": "清空输入",
    "scroll": "滚动到元素",
    "select": "选择选项",
    "check": "勾选",
    "uncheck": "取消勾选",
    "verify": "断言可见",
}


def list_testcases(suite_id: Optional[str] = None) -> List[Dict]:
    testcases = load_all()
    if suite_id is not None:
        testcases = [tc for tc in testcases if tc.get("suite_id") == suite_id]
    testcases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return testcases


def get_testcase(tc_id: str) -> Optional[Dict]:
    return get_by_id(tc_id)


def create_testcase(name: str, priority: str, description: str,
                    script: str, steps: List[Dict],
                    source: str = "recording",
                    suite_id: str = "") -> Dict:
    if not suite_id:
        raise ValueError("create_testcase 必须指定 suite_id")
    tc: Dict = {
        "id": str(uuid.uuid4()),
        "name": name,
        "priority": priority,
        "description": description,
        "script": script,
        "source": source,
        "steps": steps,
        "suite_id": suite_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    save(tc)
    _touch_suite(suite_id)
    return tc


def update_testcase(tc_id: str, name: str, priority: str,
                    description: str, script: str,
                    steps: List[Dict]) -> Optional[Dict]:
    tc = get_by_id(tc_id)
    if tc is None:
        return None
    suite_id = tc.get("suite_id")
    tc["name"] = name
    tc["priority"] = priority
    tc["description"] = description
    tc["script"] = script
    tc["steps"] = steps
    tc["updated_at"] = datetime.now().isoformat()
    save(tc)
    _touch_suite(suite_id)
    return tc


def delete_testcase(tc_id: str) -> None:
    tc = get_by_id(tc_id)
    suite_id = tc.get("suite_id") if tc else None
    delete(tc_id)
    _touch_suite(suite_id)


def list_playback_history(tc_id: str, limit: int = 5) -> List[Dict]:
    from streamlit_app.utils.playback_history import list_for_tc
    return list_for_tc(tc_id, limit=limit)


def _touch_suite(suite_id: Optional[str]) -> None:
    """把套件 updated_at 刷为 now()。套件不存在时静默忽略。"""
    if not suite_id:
        return
    suite = suite_store.get_by_id(suite_id)
    if suite is None:
        return
    suite_store.save(suite)


def validate_steps(rows: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """校验并规范化步骤行。

    rows 元素字段: action / selector / value
    返回 (cleaned_steps, errors)。cleaned_steps 每项: {id, action, selector, value, description}。
    """
    errors: List[str] = []
    cleaned: List[Dict] = []
    for idx, row in enumerate(rows, start=1):
        action = str(row.get("action", "")).strip()
        selector = str(row.get("selector", "")).strip()
        value = str(row.get("value", "")).strip()
        if not action:
            errors.append(f"第 {idx} 行：操作不能为空")
            continue
        if action not in ACTION_OPTIONS:
            errors.append(f"第 {idx} 行：未知操作「{action}」")
            continue
        if action == "navigate":
            if not value and not selector:
                errors.append(f"第 {idx} 行：操作「navigate」必须填写 URL（值或选择器）")
                continue
        elif action in ("fill", "select"):
            if not value:
                errors.append(f"第 {idx} 行：操作「{action}」必须填写值")
                continue
            if not selector:
                errors.append(f"第 {idx} 行：操作「{action}」必须填写选择器")
                continue
        else:
            if not selector:
                errors.append(f"第 {idx} 行：操作「{action}」必须填写选择器")
                continue
        cleaned.append({
            "id": str(uuid.uuid4()),
            "action": action,
            "selector": selector,
            "value": value,
            "description": ACTION_DESC_MAP.get(action, "步骤"),
        })
    return cleaned, errors
