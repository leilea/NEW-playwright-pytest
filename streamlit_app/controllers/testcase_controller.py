"""测试用例相关业务编排。

未来 API 对应：
- load_testcase_detail   → GET   /api/testcases/:id
- save_testcase_steps    → PATCH /api/testcases/:id/steps
- delete_testcase_clean  → DELETE /api/testcases/:id
"""
from typing import Dict, List, Optional, Tuple

from streamlit_app.services.testcase_service import (
    PRIORITY_MAP,
    get_testcase,
    update_testcase,
    delete_testcase,
    list_playback_history,
    validate_steps,
)
from streamlit_app.services.script_generator import generate_script


def load_testcase_detail(tc_id: str) -> Optional[Dict]:
    """加载详情页所需数据（含派生字段），返回新 dict，不修改原对象。"""
    tc = get_testcase(tc_id)
    if not tc:
        return None
    history = list_playback_history(tc_id, limit=1)
    if not history:
        latest_badge = "❓ 未回放"
    else:
        latest_badge = {
            "passed": "🟢 通过",
            "failed": "🔴 失败",
            "error": "⚠️ 错误",
        }.get(history[0].get("status"), "❓ 未知")
    return {
        **tc,
        "priority_label": PRIORITY_MAP.get(tc.get("priority", ""), tc.get("priority", "")),
        "source_badge": "🎬 录制" if tc.get("source") == "recording" else tc.get("source", ""),
        "latest_badge": latest_badge,
    }


def save_testcase_steps(tc_id: str,
                        rows: List[Dict]) -> Tuple[bool, List[str]]:
    """详情页步骤保存入口：校验→生成脚本→持久化。返回 (success, errors)。"""
    new_steps, errors = validate_steps(rows)
    if errors:
        return False, errors
    new_script = generate_script(new_steps)
    tc = get_testcase(tc_id)
    if tc is None:
        return False, [f"用例 {tc_id} 不存在"]
    update_testcase(
        tc_id,
        tc["name"],
        tc["priority"],
        tc.get("description", ""),
        new_script,
        new_steps,
    )
    return True, []


def delete_testcase_clean(tc_id: str,
                          playback_handle: Optional[Dict] = None,
                          playback_running: Optional[Dict] = None,
                          playback_logs: Optional[Dict] = None,
                          playback_result: Optional[Dict] = None) -> None:
    """删除用例并清理可能存在的回放 session state。"""
    if playback_handle is not None:
        playback_handle.pop(tc_id, None)
    if playback_running is not None:
        playback_running.pop(tc_id, None)
    if playback_logs is not None:
        playback_logs.pop(tc_id, None)
    if playback_result is not None:
        playback_result.pop(tc_id, None)
    delete_testcase(tc_id)
