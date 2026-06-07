## 1. 类型模块

- [x] 1.1 创建 `streamlit_app/types/__init__.py`（空）
- [x] 1.2 创建 `streamlit_app/types/testcase_state.py`：定义 `TestcaseView(str, Enum)` 4 个值 + `TestcaseSessionState(TypedDict)` 13 个字段 + `DEFAULT_TESTCASE_SESSION_STATE()` 工厂函数

## 2. 改造 page_testcases.py

- [x] 2.1 在 `streamlit_app/page_testcases.py` 顶部追加 `from streamlit_app.types.testcase_state import TestcaseView, DEFAULT_TESTCASE_SESSION_STATE`
- [x] 2.2 将 12 个 `if "tc_*" not in st.session_state` 块替换为 1 个 `_init_session_state()` 函数，内部遍历 `DEFAULT_TESTCASE_SESSION_STATE()` 设置缺失键
- [x] 2.3 将 `go_suite_list()` / `go_case_list()` / `go_recording()` / `go_detail()` 中对 `tc_view` 的字符串赋值改为 `TestcaseView.*` 枚举值
- [x] 2.4 业务代码中出现 `st.session_state.tc_view == "suite_list"` / `== "case_list"` / `== "detail"` / `== "recording"` 的字符串比较保持原状（依赖 `str` 继承兼容性）

## 3. 验证

- [x] 3.1 `python -c "import ast; ast.parse(open('streamlit_app/page_testcases.py', encoding='utf-8').read())"` 语法检查通过
- [x] 3.2 `python -c "from streamlit_app.types.testcase_state import TestcaseView, DEFAULT_TESTCASE_SESSION_STATE, TestcaseSessionState; s = DEFAULT_TESTCASE_SESSION_STATE(); print(s['tc_view'], type(s['tc_view']))"` 验证工厂函数返回 `TestcaseView` 枚举
- [x] 3.3 启动 streamlit 切换到「测试用例」页面，逐个视图（套件列表 / 用例列表 / 详情 / 录制）切换验证状态机正常工作
