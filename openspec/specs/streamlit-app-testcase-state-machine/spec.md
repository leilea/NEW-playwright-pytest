# streamlit-app-testcase-state-machine 规范

## 目的
待定 - 由归档变更 explicit-testcase-state-machine 创建。归档后请更新目的。
## 需求
### 需求:测试用例页视图必须用 TestcaseView 枚举表达

测试用例页的 `tc_view` 会话字段必须使用 `TestcaseView` 枚举表达，仅允许以下 4 个值：`SUITE_LIST` / `CASE_LIST` / `DETAIL` / `RECORDING`。禁止用裸字符串字面量（如 `"suite_list"`）直接给 `tc_view` 赋值。

#### 场景:跳转函数用枚举值
- **当** 任何跳转函数（`go_suite_list` / `go_case_list` / `go_recording` / `go_detail`）给 `tc_view` 赋值
- **那么** 必须使用 `TestcaseView.SUITE_LIST` / `CACE_LIST` / `RECORDING` / `DETAIL` 之一，不得使用裸字符串

#### 场景:枚举值与原字符串字面量等价
- **当** 业务代码中出现 `st.session_state.tc_view == "suite_list"` 形式的字符串比较
- **那么** 该比较必须仍然返回 True（因为 `TestcaseView` 继承自 `str`）

#### 场景:枚举定义位置唯一
- **当** 项目中存在 `TestcaseView` 定义
- **那么** 该定义必须位于 `streamlit_app/types/testcase_state.py`，不得在 page 文件内重复定义

### 需求:会话状态必须用 TestcaseSessionState TypedDict 表达

`streamlit_app/page_testcases.py` 引用的所有 `st.session_state.tc_*` 字段必须全部在 `TestcaseSessionState` TypedDict 中显式声明其类型；任何新增字段必须先加到 TypedDict 后才能在代码中使用。

#### 场景:12 个字段全部声明
- **当** 检查 `TestcaseSessionState` 定义
- **那么** 必须至少包含以下 13 个字段：`tc_view` / `tc_active_suite_id` / `tc_suite_dialog` / `tc_suite_editing_id` / `tc_editing_id` / `tc_detail_id` / `tc_show_dialog` / `tc_auto_created` / `tc_recording` / `tc_playback_running` / `tc_playback_handle` / `tc_playback_logs` / `tc_playback_result`
- **并且** 每个字段必须有显式类型注解

#### 场景:初始化用工厂函数
- **当** `page_testcases.py` 启动时初始化 session_state
- **那么** 必须通过 `DEFAULT_TESTCASE_SESSION_STATE()` 工厂函数获取默认值，不得用 13 个独立的 if-not-in 块

#### 场景:字段名稳定
- **当** TypedDict 字段被定义
- **那么** 字段名（如 `tc_active_suite_id`）必须与原有 `st.session_state.tc_active_suite_id` 字符串键完全一致
- **并且** 改名必须作为单独的破坏性变更提案，不在本变更范围内

