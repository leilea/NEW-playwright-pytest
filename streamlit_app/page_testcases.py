"""
测试用例 UI 页面（Streamlit）。
- 业务逻辑在 streamlit_app/services/
- 跨页面编排在 streamlit_app/controllers/
- 未来迁移至 TypeScript / Vue 时，仅本文件及 page_*.py 需重写
"""
import os
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from streamlit_app.utils.config_manager import load_env, get_current_user

from streamlit_app.types.testcase_state import (
    DEFAULT_TESTCASE_SESSION_STATE,
    TestcaseView,
)

from streamlit_app.services.testcase_service import (
    list_testcases,
    get_testcase,
    create_testcase,
    update_testcase,
    list_playback_history,
    ACTION_OPTIONS,
    PRIORITY_MAP,
    PRIORITY_OPTIONS,
)
from streamlit_app.services.suite_service import get_suite
from streamlit_app.services.recording_service import (
    get_recording_result,
    stop_recording,
)
from streamlit_app.services.playback_service import (
    playback_stream,
    stop_playback,
    NAV_TIMEOUT_MS,
    ELEM_TIMEOUT_MS,
    MAX_TIMEOUT_S,
    NAV_MIN_MS,
    NAV_MAX_MS,
    ELEM_MIN_MS,
    ELEM_MAX_MS,
    VALID_BROWSERS,
)
from streamlit_app.controllers.testcase_controller import (
    load_testcase_detail,
    save_testcase_steps,
    delete_testcase_clean,
)
from streamlit_app.controllers.suite_controller import (
    load_suite_list_with_count,
    create_suite_form_data,
    update_suite_form_data,
    delete_suite_with_confirm,
)

if "tc_view" not in st.session_state:
    st.session_state.tc_view = TestcaseView.SUITE_LIST


# ==================== SUITE TABLE — pure constants & helpers ====================
# 设计：列定义、列宽、页大小均为模块级常量；行映射、分页、动作派发为纯函数。
# 迁移到 TypeScript / Vue 时：
#   SUITE_TABLE_COLUMNS  → <el-table :columns="columns" />
#   SUITE_TABLE_WIDTHS   → 同一份，表格自动布局时可丢弃
#   SUITE_PAGE_SIZE      → 复制为常量
#   _row_for_suite       → 单元测试 + 翻译为 <SuiteRow :suite :index />
#   _paginate            → 单元测试 + 翻译为 computed
#   _handle_suite_action → 单元测试 + 翻译为 methods.onRowAction
# 数据切片 / 列宽 / 动作入口集中在这一段，业务 UI 渲染段不再混入逻辑。

SUITE_TABLE_COLUMNS = [
    {"key": "_index",     "label": "序号",     "width": 0.5},
    {"key": "name",       "label": "系统名称", "width": 3.0},
    {"key": "version",    "label": "版本",     "width": 1.0},
    {"key": "case_count", "label": "用例数",   "width": 1.0},
    {"key": "created_by", "label": "创建人",   "width": 1.5},
    {"key": "updated_at", "label": "更新时间", "width": 1.5},
    {"key": "_actions",   "label": "操作",     "width": 3.0},
]
SUITE_TABLE_WIDTHS = [c["width"] for c in SUITE_TABLE_COLUMNS]
SUITE_PAGE_SIZE = 10


# ==================== CASE TABLE — pure constants & helpers ====================
# 与 SUITE TABLE 同构：常量定义列 / 宽 / 页大小；纯函数做行映射与动作派发。
# 迁移到 TypeScript / Vue 时：
#   CASE_TABLE_COLUMNS   → <el-table :columns="columns" />
#   CASE_TABLE_WIDTHS    → 同一份
#   CASE_PAGE_SIZE       → 复制为常量
#   _row_for_case        → 单元测试 + <CaseRow :case :index />
#   _paginate (复用)     → computed
#   _handle_case_action  → methods.onRowAction
# 操作列用 st.selectbox 占位符 "操作..." 触发 3 个动作 (查看/修改/删除)，
# 比 3 按钮节约 2 个列宽，描述列因此能从 1.5 → 3.0。

CASE_TABLE_COLUMNS = [
    {"key": "_index",      "label": "序号",     "width": 0.5},
    {"key": "name",        "label": "用例名称", "width": 2.5},
    {"key": "priority",    "label": "优先级",   "width": 0.8},
    {"key": "source",      "label": "来源",     "width": 0.7},
    {"key": "steps",       "label": "步骤数",   "width": 0.6},
    {"key": "description", "label": "描述",     "width": 3.0},
    {"key": "created_at",  "label": "创建时间", "width": 1.4},
    {"key": "_actions",    "label": "操作",     "width": 1.0},
]
CASE_TABLE_WIDTHS = [c["width"] for c in CASE_TABLE_COLUMNS]
CASE_PAGE_SIZE = 10


def _row_for_suite(s: dict, global_index: int) -> dict:
    """把一个 suite dict 转成 UI 行所需的扁平字典。

    全局序号 `global_index` 由调用方传入（已含分页偏移），保证序号跨页连续。
    """
    return {
        "_index":     global_index,
        "name":       s.get("name", ""),
        "version":    s.get("version", ""),
        "case_count": int(s.get("case_count", 0) or 0),
        "created_by": s.get("created_by", ""),
        "updated_at": (s.get("updated_at", "") or "")[:16].replace("T", " "),
        "_id":        s["id"],
    }


def _paginate(items: list, page: int, page_size: int) -> tuple[int, int, list]:
    """分页：返回 (total_pages, safe_page, page_items)。

    `page` 越界时夹紧到合法范围；空列表返回 1 页 + 空切片，UI 不报 IndexError。
    """
    total_pages = max(1, (len(items) + page_size - 1) // page_size)
    safe_page = min(max(1, int(page)), total_pages)
    offset = (safe_page - 1) * page_size
    return total_pages, safe_page, items[offset:offset + page_size]


def _handle_suite_action(action: str, suite_id: str) -> None:
    """套件行操作统一入口：enter / edit / request_delete。

    不直接调用 `delete_suite_with_confirm` —— 删除需二次确认，由渲染段处理。
    """
    if action == "enter":
        go_case_list(suite_id)
        st.rerun()
    elif action == "edit":
        st.session_state.tc_suite_dialog = "edit"
        st.session_state.tc_suite_editing_id = suite_id
        st.rerun()
    elif action == "request_delete":
        st.session_state[f"_pending_delete_suite_{suite_id}"] = True
        st.rerun()
    else:
        raise ValueError(f"未知套件动作: {action!r}")


def _row_for_case(tc: dict, global_index: int) -> dict:
    """把一个 testcase dict 转成 UI 行所需的扁平字典。

    全局序号 `global_index` 由调用方传入（已含分页偏移），保证序号跨页连续。
    """
    priority_raw = tc.get("priority", "")
    return {
        "_index":      global_index,
        "name":        tc.get("name", ""),
        "priority":    PRIORITY_MAP.get(priority_raw, priority_raw),
        "source":      "🎬 录制" if tc.get("source") == "recording" else "—",
        "steps":       len(tc.get("steps", []) or []),
        "description": (tc.get("description", "") or "")[:50],
        "created_at":  (tc.get("created_at", "") or "")[:16].replace("T", " "),
        "_id":         tc["id"],
    }


def _handle_case_action(action: str, tc_id: str) -> None:
    """测试用例行操作统一入口：view / edit / delete。

    - view  → 进入详情页
    - edit  → 进入录制页（复用现有录制流作为编辑入口）
    - delete → 直接删除并清理孤儿 selectbox state key；
               page-clamp 由渲染段处理（需要 total_pages 信息）
    """
    if action == "view":
        go_detail(tc_id)
        st.rerun()
    elif action == "edit":
        st.session_state.tc_editing_id = tc_id
        st.session_state.tc_view = TestcaseView.RECORDING
        st.rerun()
    elif action == "delete":
        delete_testcase_clean(
            tc_id,
            st.session_state.tc_playback_handle,
            st.session_state.tc_playback_running,
            st.session_state.tc_playback_logs,
            st.session_state.tc_playback_result,
        )
        st.session_state.pop(f"case_action_{tc_id}", None)
        st.rerun()
    else:
        raise ValueError(f"未知用例动作: {action!r}")


def _init_session_state() -> None:
    """按 `DEFAULT_TESTCASE_SESSION_STATE()` 工厂函数为缺失字段补缺省。"""
    for key, default in DEFAULT_TESTCASE_SESSION_STATE().items():
        if key not in st.session_state:
            st.session_state[key] = default


_init_session_state()


def reset_recording():
    if st.session_state.tc_recording:
        stop_recording(st.session_state.tc_recording)
    st.session_state.tc_recording = None


def go_suite_list():
    reset_recording()
    st.session_state.tc_view = TestcaseView.SUITE_LIST
    st.session_state.tc_editing_id = None
    st.session_state.tc_show_dialog = False
    st.session_state.tc_detail_id = None
    st.session_state.tc_active_suite_id = None
    st.session_state.tc_suite_dialog = None
    st.session_state.tc_suite_editing_id = None


def go_case_list(suite_id: str):
    reset_recording()
    st.session_state.tc_view = TestcaseView.CASE_LIST
    st.session_state.tc_active_suite_id = suite_id
    st.session_state.tc_editing_id = None
    st.session_state.tc_show_dialog = False
    st.session_state.tc_detail_id = None
    st.session_state.tc_suite_dialog = None
    st.session_state.tc_suite_editing_id = None


def go_recording():
    st.session_state.tc_view = TestcaseView.RECORDING
    st.session_state.tc_show_dialog = False


def go_detail(tc_id: str):
    reset_recording()
    st.session_state.tc_view = TestcaseView.DETAIL
    st.session_state.tc_detail_id = tc_id
    st.session_state.tc_editing_id = None
    st.session_state.tc_show_dialog = False


# ==================== PLAYBACK PANEL ====================
def _render_playback_panel(tc: dict, in_detail: bool = False):
    tc_id = tc["id"]
    running = st.session_state.tc_playback_running.get(tc_id, False)
    logs = st.session_state.tc_playback_logs.get(tc_id, [])
    last_result = st.session_state.tc_playback_result.get(tc_id)
    is_recording_src = tc.get("source") == "recording"

    prefix = "detail_" if in_detail else ""
    panel_label = f"🎬 回放：{tc.get('name', '')}"
    with st.expander(panel_label, expanded=running or last_result is not None):
        if not is_recording_src:
            st.caption("⚠️ 该用例来源不是录制，脚本可能不是标准 Playwright 模块。仍可尝试回放")

        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            browser = st.selectbox(
                "浏览器",
                options=list(VALID_BROWSERS),
                index=0,
                key=f"{prefix}pb_browser_{tc_id}",
                disabled=running,
            )
        with col2:
            nav_timeout_s = st.slider(
                "页面加载超时 (秒)",
                min_value=NAV_MIN_MS // 1000,
                max_value=NAV_MAX_MS // 1000,
                value=NAV_TIMEOUT_MS // 1000,
                key=f"{prefix}pb_nav_timeout_{tc_id}",
                disabled=running,
            )
        with col3:
            elem_timeout_s = st.slider(
                "元素等待超时 (秒)",
                min_value=ELEM_MIN_MS // 1000,
                max_value=ELEM_MAX_MS // 1000,
                value=ELEM_TIMEOUT_MS // 1000,
                key=f"{prefix}pb_elem_timeout_{tc_id}",
                disabled=running,
            )
        with col4:
            headless = st.checkbox(
                "无头模式",
                value=True,
                key=f"{prefix}pb_headless_{tc_id}",
                disabled=running,
            )

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            start_clicked = st.button(
                "▶️ 开始回放",
                type="primary",
                key=f"{prefix}pb_start_{tc_id}",
                disabled=running,
                width='stretch',
            )
        with btn_col2:
            stop_clicked = st.button(
                "⏹️ 停止",
                key=f"{prefix}pb_stop_{tc_id}",
                disabled=not running,
                width='stretch',
            )

        if start_clicked:
            st.session_state.tc_playback_running[tc_id] = True
            st.session_state.tc_playback_logs[tc_id] = []
            st.session_state.tc_playback_result[tc_id] = None
            st.rerun()

        if stop_clicked and tc_id in st.session_state.tc_playback_handle:
            stop_playback(st.session_state.tc_playback_handle[tc_id])
            st.session_state.tc_playback_handle.pop(tc_id, None)
            st.session_state.tc_playback_running[tc_id] = False
            st.rerun()

        if st.session_state.tc_playback_running.get(tc_id) and not st.session_state.tc_playback_handle.get(tc_id):
            try:
                gen = playback_stream(
                    tc,
                    browser=browser,
                    headless=headless,
                    nav_timeout_ms=nav_timeout_s * 1000,
                    elem_timeout_ms=elem_timeout_s * 1000,
                )
                result_holder = {"value": None}

                def _consume(g, holder):
                    try:
                        for line in g:
                            logs.append(line)
                        holder["value"] = None
                    except StopIteration as e:
                        holder["value"] = e.value
                    except Exception as ex:
                        holder["value"] = {"status": "error", "error": str(ex), "screenshot": None}

                import threading as _th
                th = _th.Thread(target=_consume, args=(gen, result_holder), daemon=True)
                th.start()

                st.session_state.tc_playback_handle[tc_id] = {
                    "thread": th,
                    "gen": gen,
                    "result_holder": result_holder,
                }
            except Exception as e:
                st.error(f"启动回放失败: {e}")
                st.session_state.tc_playback_running[tc_id] = False

        if st.session_state.tc_playback_handle.get(tc_id):
            handle = st.session_state.tc_playback_handle[tc_id]
            th = handle["thread"]
            if not th.is_alive():
                st.session_state.tc_playback_running[tc_id] = False
                result = handle["result_holder"]["value"]
                st.session_state.tc_playback_result[tc_id] = result
                st.session_state.tc_playback_handle.pop(tc_id, None)
                st.rerun()

        current_logs = st.session_state.tc_playback_logs.get(tc_id, [])
        if current_logs:
            display = "".join(current_logs[-200:])
            st.code(display, language="bash")

        result = st.session_state.tc_playback_result.get(tc_id)
        if result:
            status = result.get("status", "unknown")
            duration = result.get("duration_ms", 0)
            exit_code = result.get("exit_code")
            browser_used = result.get("browser", "")
            error = result.get("error")
            screenshot = result.get("screenshot")

            st.divider()
            if status == "passed":
                st.success(f"✅ 通过  耗时 {duration}ms  浏览器 {browser_used}  exit={exit_code}")
            elif status == "failed":
                st.error(f"❌ 失败  耗时 {duration}ms  浏览器 {browser_used}  exit={exit_code}  {error or ''}")
            else:
                st.warning(f"⚠️ {status}  耗时 {duration}ms  {error or ''}")

            if screenshot and Path(screenshot).exists():
                st.markdown("**失败截图：**")
                st.image(str(screenshot), width='stretch')
            elif status != "passed":
                st.caption("未捕获到截图（脚本可能在 page 创建前失败，或为录制脚本 page 作用域不可见）")

        st.divider()
        st.markdown("**最近 5 次回放历史**")
        history = list_playback_history(tc_id, limit=5)
        if not history:
            st.caption("暂无历史")
        else:
            rows = []
            for h in history:
                rows.append({
                    "时间": h.get("ts", "")[:19].replace("T", " "),
                    "状态": {"passed": "✅", "failed": "❌", "error": "⚠️"}.get(h.get("status", ""), "?"),
                    "浏览器": h.get("browser", ""),
                    "耗时(ms)": h.get("duration_ms", 0),
                    "退出码": h.get("exit_code"),
                    "错误": h.get("error") or "",
                })
            st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)


# ==================== CREATE DIALOG ====================
@st.dialog("选择用例创建方式")
def show_create_dialog():
    st.caption("请选择一种创建方式来开始创建测试用例")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("🔧")
            st.subheader("手动录入")
            st.caption("可视化元素定位器，支持多种定位策略")
            st.caption("🔒 暂时关闭")
            st.button("选择", key="dlg_manual", disabled=True, width='stretch')

    with col2:
        with st.container(border=True):
            st.markdown("🎬")
            st.subheader("Playwright录制")
            st.caption("录制页面操作生成用例")
            st.caption("✅ 正常")
            if st.button("选择", key="dlg_record", type="primary", width='stretch'):
                go_recording()
                st.rerun()

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.markdown("✅")
            st.subheader("AI智能生成")
            st.caption("自然语言描述生成测试用例")
            st.caption("🔒 暂时关闭")
            st.button("选择", key="dlg_ai", disabled=True, width='stretch')

    with col4:
        st.empty()


# ==================== SUITE DIALOGS ====================
@st.dialog("新增套件")
def show_create_suite_dialog():
    current_user = get_current_user()
    with st.form("create_suite_form", clear_on_submit=True):
        s_name = st.text_input("系统名称", max_chars=64, placeholder="例如：电商后台")
        s_version = st.text_input("版本号", max_chars=32, placeholder="例如：v1.0")
        st.text_input("创建人", value=current_user, disabled=True)
        st.caption("创建人自动取自当前登录用户")
        submitted = st.form_submit_button("保存", type="primary", width='stretch')

    if submitted:
        success, msg, _suite = create_suite_form_data(s_name, s_version, current_user)
        if success:
            st.success("新增成功")
            st.session_state.tc_suite_dialog = None
            st.rerun()
        else:
            st.error(msg)


@st.dialog("修改套件")
def show_edit_suite_dialog(suite_id: str):
    suite = get_suite(suite_id)
    if suite is None:
        st.error("套件不存在或已被删除")
        if st.button("关闭", key="edit_suite_close_missing"):
            st.session_state.tc_suite_dialog = None
            st.session_state.tc_suite_editing_id = None
            st.rerun()
        return

    with st.form(f"edit_suite_form_{suite_id}"):
        s_name = st.text_input("系统名称", value=suite.get("name", ""), max_chars=64)
        s_version = st.text_input("版本号", value=suite.get("version", ""), max_chars=32)
        st.text_input("创建人", value=suite.get("created_by", ""), disabled=True)
        submitted = st.form_submit_button("保存", type="primary", width='stretch')

    if submitted:
        success, msg, _suite = update_suite_form_data(suite_id, s_name, s_version)
        if success:
            st.success("已保存")
            st.session_state.tc_suite_dialog = None
            st.session_state.tc_suite_editing_id = None
            st.rerun()
        else:
            st.error(msg)


# ==================== DETAIL VIEW ====================
def render_detail_view():
    tc_id = st.session_state.tc_detail_id
    tc = load_testcase_detail(tc_id)
    if not tc:
        st.error("用例不存在或已被删除")
        if st.button("← 返回用例列表", key="detail_back_err"):
            if st.session_state.tc_active_suite_id:
                go_case_list(st.session_state.tc_active_suite_id)
            else:
                go_suite_list()
            st.rerun()
        return

    c1, c2, c3 = st.columns([1, 1, 4])
    with c1:
        if st.button("← 返回", key="detail_back"):
            if st.session_state.tc_active_suite_id:
                go_case_list(st.session_state.tc_active_suite_id)
            else:
                go_suite_list()
            st.rerun()
    with c2:
        if st.button("编辑", key="detail_edit"):
            st.session_state.tc_view = TestcaseView.RECORDING
            st.session_state.tc_editing_id = tc_id
            st.rerun()
    with c3:
        if st.button("删除", key="detail_delete", type="secondary"):
            delete_testcase_clean(
                tc_id,
                st.session_state.tc_playback_handle,
                st.session_state.tc_playback_running,
                st.session_state.tc_playback_logs,
                st.session_state.tc_playback_result,
            )
            if st.session_state.tc_active_suite_id:
                go_case_list(st.session_state.tc_active_suite_id)
            else:
                go_suite_list()
            st.rerun()

    st.title(tc.get("name", ""))
    st.caption(
        f"{tc.get('priority_label', '')}  •  {tc.get('source_badge', '')}  •  "
        f"最新 {tc.get('latest_badge', '')}  •  创建 {tc.get('created_at', '')[:10]}"
    )
    if tc.get("description"):
        st.markdown(f"**描述**: {tc.get('description', '')}")

    tab_steps, tab_script = st.tabs(["📋 步骤列表", "📜 脚本预览"])
    with tab_steps:
        steps = tc.get("steps", [])
        rows = []
        for s in steps:
            rows.append({
                "操作": s.get("action", ""),
                "选择器": s.get("selector", ""),
                "值": s.get("value", ""),
            })
        if not rows:
            rows = [{"操作": "navigate", "选择器": "", "值": ""}]
        df = pd.DataFrame(rows)

        edited = st.data_editor(
            df,
            column_config={
                "操作": st.column_config.SelectboxColumn("操作", options=ACTION_OPTIONS, required=True),
                "选择器": st.column_config.TextColumn("选择器"),
                "值": st.column_config.TextColumn("值"),
            },
            num_rows="dynamic",
            hide_index=True,
            key=f"steps_editor_{tc_id}",
            width='stretch',
        )

        if st.button("💾 保存修改", type="primary", key=f"save_steps_{tc_id}"):
            rows_to_save = edited.to_dict('records')
            success, errors = save_testcase_steps(tc_id, rows_to_save)
            if not success:
                for e in errors:
                    st.error(e)
            else:
                st.success("已保存并同步脚本")
                st.rerun()

    with tab_script:
        st.code(tc.get("script", ""), language="python")
        st.caption("脚本由步骤列表自动生成。修改步骤后请在「步骤列表」tab 保存。")

    st.divider()
    _render_playback_panel(tc, in_detail=True)

    st.divider()
    st.markdown("**🎬 回放历史 (最近 5 次)**")
    history = list_playback_history(tc_id, limit=5)
    if history:
        h_rows = []
        for h in history:
            h_rows.append({
                "时间": h.get("ts", "")[:19].replace("T", " "),
                "状态": {"passed": "✅", "failed": "❌", "error": "⚠️"}.get(h.get("status", ""), "?"),
                "浏览器": h.get("browser", ""),
                "耗时(ms)": h.get("duration_ms", 0),
                "退出码": h.get("exit_code"),
            })
        st.dataframe(pd.DataFrame(h_rows), width='stretch', hide_index=True)
    else:
        st.caption("暂无历史")


# ==================== SUITE LIST VIEW ====================
def render_suite_list_view():
    st.title("测试用例 / 套件")
    st.caption("套件是测试用例的容器，按「系统名称 + 版本号」组织用例。")

    if st.button("➕ 新增", type="primary", key="suite_create_btn", width='stretch'):
        st.session_state.tc_suite_dialog = "create"
        st.rerun()

    if st.session_state.tc_suite_dialog == "create":
        show_create_suite_dialog()
    elif st.session_state.tc_suite_dialog == "edit" and st.session_state.tc_suite_editing_id:
        show_edit_suite_dialog(st.session_state.tc_suite_editing_id)

    suites = load_suite_list_with_count()

    if not suites:
        st.info("暂无套件，点击「➕ 新增」按钮开始创建。")
        return

    total_pages, page, page_items = _paginate(
        suites, st.session_state.tc_suite_page, SUITE_PAGE_SIZE
    )
    st.session_state.tc_suite_page = page
    offset = (page - 1) * SUITE_PAGE_SIZE

    st.subheader(f"套件列表 ({len(suites)})")

    # 表头
    header_cols = st.columns(SUITE_TABLE_WIDTHS)
    for col, c in zip(header_cols, SUITE_TABLE_COLUMNS):
        col.markdown(f"**{c['label']}**")
    st.divider()

    # 数据行
    for row_pos, s in enumerate(page_items):
        row = _row_for_suite(s, offset + row_pos + 1)
        cols = st.columns(SUITE_TABLE_WIDTHS)

        cols[0].text(str(row["_index"]))

        cols[1].button(
            row["name"],
            key=f"suite_name_btn_{row['_id']}",
            type="tertiary",
            width='stretch',
            on_click=go_case_list,
            args=(row["_id"],),
        )

        cols[2].text(row["version"])
        cols[3].text(str(row["case_count"]))
        cols[4].text(row["created_by"])
        cols[5].text(row["updated_at"])

        # 操作列：进入 / 修改 / 删除
        ecols = cols[6].columns(3)
        ecols[0].button(
            "进入",
            key=f"suite_enter_{row['_id']}",
            width='stretch',
            on_click=_handle_suite_action,
            args=("enter", row["_id"]),
        )
        ecols[1].button(
            "修改",
            key=f"suite_edit_{row['_id']}",
            width='stretch',
            on_click=_handle_suite_action,
            args=("edit", row["_id"]),
        )
        is_empty = row["case_count"] == 0
        delete_help = None if is_empty else f"套件内还有 {row['case_count']} 条用例，请先删除"
        ecols[2].button(
            "删除",
            key=f"suite_delete_{row['_id']}",
            type="secondary",
            width='stretch',
            disabled=not is_empty,
            help=delete_help,
            on_click=_handle_suite_action,
            args=("request_delete", row["_id"]),
        )

        # 二次确认（保持内联，单调用方，抽离 ROI 低）
        pending_key = f"_pending_delete_suite_{row['_id']}"
        if st.session_state.get(pending_key):
            st.warning(
                f"确定删除「{row['name']} {row['version']}」？该操作不可撤销。"
            )
            cc1, cc2, _ = st.columns([1, 1, 6])
            with cc1:
                if st.button(
                    "确认删除",
                    key=f"suite_delete_confirm_{row['_id']}",
                    type="primary",
                ):
                    ok, msg = delete_suite_with_confirm(row["_id"])
                    if ok:
                        st.success("已删除")
                        st.session_state.pop(pending_key, None)
                        # 防止当前页越界
                        st.session_state.tc_suite_page = min(page, max(1, total_pages - 1))
                        st.rerun()
                    else:
                        st.error(msg)
            with cc2:
                if st.button("取消", key=f"suite_delete_cancel_{row['_id']}"):
                    st.session_state.pop(pending_key, None)
                    st.rerun()

    # 分页栏
    if total_pages > 1:
        nav = st.columns([1, 2, 1, 4])
        nav[0].button(
            "‹ 上一页",
            key="suite_prev",
            disabled=page == 1,
            width='stretch',
            on_click=lambda: st.session_state.update(tc_suite_page=page - 1),
        )
        nav[1].markdown(
            f"<div style='text-align:center;color:var(--color-text-muted);"
            f"font-size:var(--text-sm);padding-top:0.4rem'>"
            f"第 {page} / {total_pages} 页 · 共 {len(suites)} 条</div>",
            unsafe_allow_html=True,
        )
        nav[2].button(
            "下一页 ›",
            key="suite_next",
            disabled=page == total_pages,
            width='stretch',
            on_click=lambda: st.session_state.update(tc_suite_page=page + 1),
        )


# ==================== LIST VIEW (FILTERED) ====================
def render_list_view():
    suite_id = st.session_state.tc_active_suite_id
    suite = get_suite(suite_id) if suite_id else None
    if suite is None:
        st.error("套件不存在或已被删除")
        if st.button("← 返回套件列表", key="case_list_back_err"):
            go_suite_list()
            st.rerun()
        return

    bc1, bc2 = st.columns([1, 8])
    with bc1:
        if st.button("← 返回套件列表", key="case_list_back"):
            go_suite_list()
            st.rerun()
    with bc2:
        st.caption(f"套件 / {suite.get('name', '')} {suite.get('version', '')}")

    st.title(f"测试用例 — {suite.get('name', '')}")

    auto_name = st.session_state.pop("tc_auto_created", "")
    if auto_name:
        st.success(f"✅ 录制完成，已自动创建用例「{auto_name}」")

    col_btn, col_info = st.columns([2, 8])
    with col_btn:
        if st.button("创建用例", type="primary", icon="➕", width='stretch'):
            st.session_state.tc_show_dialog = True
            st.rerun()

    if st.session_state.tc_show_dialog:
        show_create_dialog()

    testcases = list_testcases(suite_id=suite_id)

    if not testcases:
        st.info("该套件下暂无测试用例，点击「创建用例」按钮开始创建。")
        return

    total_pages, page, page_items = _paginate(
        testcases, st.session_state.tc_case_page, CASE_PAGE_SIZE
    )
    st.session_state.tc_case_page = page
    offset = (page - 1) * CASE_PAGE_SIZE

    st.subheader(f"用例列表 ({len(testcases)})")

    # 表头
    header_cols = st.columns(CASE_TABLE_WIDTHS)
    for col, c in zip(header_cols, CASE_TABLE_COLUMNS):
        col.markdown(f"**{c['label']}**")
    st.divider()

    # 数据行
    action_options = ["操作...", "查看", "修改", "删除"]
    for row_pos, tc in enumerate(page_items):
        row = _row_for_case(tc, offset + row_pos + 1)
        cols = st.columns(CASE_TABLE_WIDTHS)

        cols[0].text(str(row["_index"]))

        cols[1].button(
            row["name"],
            key=f"case_name_btn_{row['_id']}",
            type="tertiary",
            width='stretch',
            on_click=go_detail,
            args=(row["_id"],),
        )

        cols[2].text(row["priority"])
        cols[3].text(row["source"])
        cols[4].text(str(row["steps"]))
        cols[5].text(row["description"])
        cols[6].text(row["created_at"])

        # 操作列：单 selectbox 触发 3 动作
        action_key = f"case_action_{row['_id']}"
        if action_key not in st.session_state:
            st.session_state[action_key] = action_options[0]
        selected = cols[7].selectbox(
            "操作",
            action_options,
            key=action_key,
            label_visibility="collapsed",
        )
        if selected != action_options[0]:
            st.session_state[action_key] = action_options[0]
            _handle_case_action(selected, row["_id"])

    # 分页栏
    if total_pages > 1:
        nav = st.columns([1, 2, 1, 4])
        nav[0].button(
            "‹ 上一页",
            key="case_prev",
            disabled=page == 1,
            width='stretch',
            on_click=lambda: st.session_state.update(tc_case_page=page - 1),
        )
        nav[1].markdown(
            f"<div style='text-align:center;color:var(--color-text-muted);"
            f"font-size:var(--text-sm);padding-top:0.4rem'>"
            f"第 {page} / {total_pages} 页 · 共 {len(testcases)} 条</div>",
            unsafe_allow_html=True,
        )
        nav[2].button(
            "下一页 ›",
            key="case_next",
            disabled=page == total_pages,
            width='stretch',
            on_click=lambda: st.session_state.update(tc_case_page=page + 1),
        )


# ==================== RECORDING VIEW ====================
def render_recording_view():
    st.title("创建用例 — Playwright录制")

    env_vars = load_env()
    current_recording_url = env_vars.get("RECORDING_URL", "").strip()
    st.text_input(
        "目标URL",
        value=current_recording_url or "(未配置，将使用 config/test_config.py 中的 base_url)",
        disabled=True,
    )
    st.caption("录制时浏览器打开的目标地址。如需修改，请在「系统配置」页面调整。")

    back_suite_id = st.session_state.tc_active_suite_id
    if st.button("← 返回用例列表"):
        if back_suite_id:
            go_case_list(back_suite_id)
        else:
            go_suite_list()
        st.rerun()

    editing_tc = None
    if st.session_state.tc_editing_id:
        editing_tc = get_testcase(st.session_state.tc_editing_id)

    with st.container(border=True):
        st.subheader("用例信息" if not editing_tc else "编辑用例信息")
        tc_name = st.text_input(
            "用例名称",
            value=editing_tc.get("name", "") if editing_tc else "",
            placeholder="例如：test_login",
        )
        tc_priority = st.selectbox(
            "优先级",
            options=PRIORITY_OPTIONS,
            index=PRIORITY_OPTIONS.index(editing_tc.get("priority", "P1")) if editing_tc else 1,
            format_func=lambda x: PRIORITY_MAP.get(x, x),
        )
        tc_description = st.text_area(
            "描述",
            value=editing_tc.get("description", "") if editing_tc else "",
            placeholder="描述该测试用例的测试目标",
            height=80,
        )

    recording = st.session_state.tc_recording
    is_recording = recording is not None

    col1, col2 = st.columns(2)
    with col1:
        if not is_recording:
            if st.button("开始录制", type="primary", icon="🔴", width='stretch'):
                env_vars = load_env()
                recording_url = env_vars.get("RECORDING_URL", "")
                if recording_url:
                    os.environ["RECORDING_URL"] = recording_url

                import importlib
                from streamlit_app.services import recording_service as _rs_mod
                importlib.reload(_rs_mod)
                rec_result = _rs_mod.start_recording()
                st.session_state.tc_recording = rec_result
                st.session_state.tc_recorded_script = ""
                st.session_state.tc_recorded_steps = []
                st.session_state.tc_recorded_stats = {}
                st.rerun()
        else:
            if st.button("停止录制", type="secondary", icon="⏹️", width='stretch'):
                stop_recording(recording)
                st.rerun()

    with col2:
        if is_recording:
            st.warning("🔴 录制中... 请在浏览器窗口中操作，完成后点击「停止录制」")

    if is_recording:
        result = get_recording_result(recording)
        if result["status"] == "recording":
            st.info("等待录制完成，请在打开的浏览器中操作...")
        elif result["status"] == "error":
            st.error(f"录制出错: {result.get('error', '未知错误')}")
            st.session_state.tc_recording = None
        elif result["status"] == "done":
            draft_name = tc_name.strip() or f"录制草稿_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            draft_desc = tc_description.strip() or "通过 Playwright 录制自动创建"
            target_suite_id = back_suite_id or ""
            if not target_suite_id:
                st.error("当前未指定套件，无法创建用例")
                st.session_state.tc_recording = None
            else:
                if editing_tc:
                    update_testcase(editing_tc["id"], draft_name, tc_priority, draft_desc, result["script"], result["steps"])
                else:
                    create_testcase(
                        draft_name,
                        tc_priority,
                        draft_desc,
                        result["script"],
                        result["steps"],
                        source="recording",
                        suite_id=target_suite_id,
                    )
                st.session_state.tc_recording = None
                st.session_state.tc_recorded_script = ""
                st.session_state.tc_recorded_steps = []
                st.session_state.tc_recorded_stats = {}
                st.session_state.tc_auto_created = draft_name
                go_case_list(target_suite_id)
                st.rerun()


# ==================== MAIN ====================
if st.session_state.tc_view == "recording":
    render_recording_view()
elif st.session_state.tc_view == "detail":
    render_detail_view()
elif st.session_state.tc_view == "case_list":
    render_list_view()
else:
    render_suite_list_view()
