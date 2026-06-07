"""测试用例页的 session state 类型契约。

提供 `TestcaseView` 枚举与 `TestcaseSessionState` TypedDict，
让 `page_testcases.py` 的状态机从"魔法字符串 + 散落 key"变成类型化契约。
"""
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypedDict


class TestcaseView(str, Enum):
    """测试用例页的 4 个顶级视图。

    继承 `str` 让 `TestcaseView.SUITE_LIST == "suite_list"` 仍为 True，
    业务代码中 `st.session_state.tc_view == "suite_list"` 这种字符串比较
    无需改写。
    """

    SUITE_LIST = "suite_list"
    CASE_LIST = "case_list"
    DETAIL = "detail"
    RECORDING = "recording"


SuiteDialogMode = Literal["create", "edit"]


class TestcaseSessionState(TypedDict, total=False):
    """测试用例页 session_state 全部 15 个字段的契约。

    `total=False` 因为所有字段都允许尚未初始化，调用方通过
    `DEFAULT_TESTCASE_SESSION_STATE()` 获取缺省值。
    """

    tc_view: TestcaseView
    tc_active_suite_id: Optional[str]
    tc_suite_dialog: Optional[SuiteDialogMode]
    tc_suite_editing_id: Optional[str]
    tc_suite_page: int
    tc_case_page: int
    tc_editing_id: Optional[str]
    tc_detail_id: Optional[str]
    tc_show_dialog: bool
    tc_auto_created: str
    tc_recording: Optional[Any]
    tc_playback_running: Dict[str, bool]
    tc_playback_handle: Dict[str, Any]
    tc_playback_logs: Dict[str, List[str]]
    tc_playback_result: Dict[str, Any]


def DEFAULT_TESTCASE_SESSION_STATE() -> TestcaseSessionState:
    """返回新会话的初始状态。每次调用返回新 dict，避免可变共享。"""
    return {
        "tc_view": TestcaseView.SUITE_LIST,
        "tc_active_suite_id": None,
        "tc_suite_dialog": None,
        "tc_suite_editing_id": None,
        "tc_suite_page": 1,
        "tc_case_page": 1,
        "tc_editing_id": None,
        "tc_detail_id": None,
        "tc_show_dialog": False,
        "tc_auto_created": "",
        "tc_recording": None,
        "tc_playback_running": {},
        "tc_playback_handle": {},
        "tc_playback_logs": {},
        "tc_playback_result": {},
    }


__all__ = [
    "TestcaseView",
    "SuiteDialogMode",
    "TestcaseSessionState",
    "DEFAULT_TESTCASE_SESSION_STATE",
]
