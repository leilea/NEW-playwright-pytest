## 为什么

`streamlit_app/page_testcases.py` 当前用 12 个独立的 `st.session_state.tc_*` 字符串/对象键拼装状态机，`tc_view` 是裸字符串 `"suite_list" | "case_list" | "detail" | "recording"`。这套隐式状态机：

1. **类型不安全**：IDE 补全不到任何字段，拼写错误只在运行时被 `if "tc_vies" not in st.session_state` 这种 None 检查兜住
2. **状态机不显式**：12 个键的合法值集合、转换规则只能靠人脑维护
3. **不利于迁移**：若后期切换到 vue-router / Pinia，状态机需要 1:1 平移，散落的字符串 key 会变成迁移事故源

本次变更把状态机显式化为 `TestcaseView` 枚举 + `TestcaseSessionState` TypedDict，把"魔法字符串"变成"类型签名"。

## 变更内容

- **新增** `streamlit_app/types/testcase_state.py`：
  - `TestcaseView` —— `str, Enum`，合法 4 个值 `SUITE_LIST | CASE_LIST | DETAIL | RECORDING`
  - `SuiteDialogMode` —— `Literal["create", "edit"]`
  - `TestcaseSessionState` —— `TypedDict`，显式声明 12 个字段及类型
  - `DEFAULT_TESTCASE_SESSION_STATE` —— 工厂函数，返回一个新会话的初始状态
- **修改** `streamlit_app/page_testcases.py`：
  - 12 个 `if "tc_*" not in st.session_state: ...` 初始化块替换为 1 行 `_init_session_state()`
  - `go_suite_list()` / `go_case_list(suite_id)` / `go_recording()` / `go_detail(tc_id)` 改用 `TestcaseView` 枚举值
  - 行为完全不变；类型注解 + 字段名集中

## 功能 (Capabilities)

### 新增功能
- `streamlit-app-testcase-state-machine`: 测试用例页的 session state 必须用 `TestcaseView` 枚举 + `TestcaseSessionState` TypedDict 表达；不允许用裸字符串字面量作视图标识；所有合法的会话字段必须在 `TypedDict` 中显式声明。

### 修改功能
- 无（不改任何业务行为；仅是状态机的显式化）

## 影响

- **代码**：`streamlit_app/types/testcase_state.py`（新）+ `streamlit_app/page_testcases.py`（局部重写 session_state 初始化与跳转函数）
- **运行时**：零依赖新增；行为完全等价
- **测试代码**：无影响
- **用户可见行为**：无变化
- **可回滚**：仅 2 个文件改动，且 12 个字段名保持原名，git revert 即可恢复
- **依赖**：需要 Python 3.8+（`TypedDict` 自 3.8 起可用）；本项目 Python 版本要求已满足
