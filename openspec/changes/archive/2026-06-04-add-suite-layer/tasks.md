## 1. 数据层

- [x] 1.1 创建 `streamlit_app/utils/suite_store.py`：实现 `load_all` / `get_by_id` / `save` / `delete` / `count_testcases(suite_id)` / `find_by_name_version(name, version)`，仿 `testcase_store.py` 风格（JSON 文件 + 临时文件原子写）
- [x] 1.2 在 `streamlit_app/utils/testcase_store.py` 末尾新增 `_migrate_default_suite()`：扫描无 `suite_id` 用例，必要时创建「默认系统」套件并挂载；`_ensure_store()` 后自动调用一次
- [x] 1.3 在 `streamlit_app/utils/testcase_store.py` 中扩展 `save` 函数：入参新增必填 `suite_id`；旧数据若 `suite_id` 缺失则保留兼容但打 warning

## 2. 配置层

- [x] 2.1 在 `streamlit_app/utils/config_manager.py` 末尾新增 `get_current_user() -> str`：返回 `os.environ.get("USER")` 或 `os.environ.get("USERNAME")` 或 `"admin"`

## 3. 服务层

- [x] 3.1 创建 `streamlit_app/services/suite_service.py`：实现 `list_suites`（带 `case_count` 字段）/ `get_suite` / `create_suite(name, version, created_by)`（含组合唯一校验）/ `update_suite(suite_id, name, version)`（含组合唯一校验）/ `delete_suite_if_empty(suite_id) -> (bool, str)`
- [x] 3.2 在 `streamlit_app/services/testcase_service.py` 中扩展 `list_testcases(suite_id: Optional[str] = None)`：可选 `suite_id` 过滤
- [x] 3.3 在 `streamlit_app/services/testcase_service.py` 中扩展 `create_testcase` 签名：新增必填 `suite_id` 参数；末尾调用 `_touch_suite(suite_id)`
- [x] 3.4 在 `streamlit_app/services/testcase_service.py` 中扩展 `update_testcase`：从旧用例读取 `suite_id` 透传；末尾调用 `_touch_suite(suite_id)`
- [x] 3.5 在 `streamlit_app/services/testcase_service.py` 中扩展 `delete_testcase`：从删除前的副本读出 `suite_id`；删除成功后调用 `_touch_suite(suite_id)`
- [x] 3.6 在 `streamlit_app/services/testcase_service.py` 中新增私有 `_touch_suite(suite_id)`：用 `suite_store.get_by_id` + `save` 把 `updated_at` 刷为 `now()`，套件不存在时静默忽略

## 4. 控制器层

- [x] 4.1 创建 `streamlit_app/controllers/suite_controller.py`：实现 `load_suite_list_with_count()`（直接转发 `suite_service.list_suites`）/ `create_suite_form_data(name, version)` / `update_suite_form_data(suite_id, name, version)` / `delete_suite_with_confirm(suite_id)`

## 5. UI 状态机扩展

- [x] 5.1 在 `streamlit_app/page_testcases.py` 顶部 session_state 初始化中追加 `tc_active_suite_id` / `tc_suite_dialog` / `tc_suite_editing_id` 三个键
- [x] 5.2 把 `tc_view` 默认值从 `"list"` 改为 `"suite_list"`；在 `go_list()` 中重命名为 `go_suite_list()` 并设为 `tc_view = "suite_list"`
- [x] 5.3 新增 `go_case_list(suite_id)` 跳转函数：设置 `tc_view = "case_list"` 与 `tc_active_suite_id`
- [x] 5.4 在 `go_suite_list()` 中清空 `tc_active_suite_id` / `tc_suite_dialog` / `tc_suite_editing_id`
- [x] 5.5 修改主入口分支：`tc_view == "suite_list"` 渲染套件列表；`tc_view == "case_list"` 渲染过滤后的用例列表；其他分支保持不变

## 6. UI — 套件列表页

- [x] 6.1 新增 `render_suite_list_view()`：标题「测试用例 / 套件」；顶部「+ 新增」按钮；`list_suites()` 拉数据
- [x] 6.2 在 `render_suite_list_view()` 中渲染套件表格：每行用 `st.container(border=True)` 包裹，列布局展示 序号 / 系统名称（可点击） / 版本号 / 用例数 / 创建人 / 上次操作时间
- [x] 6.3 系统名称列用 `st.button(name, key=..., type="tertiary")` 模拟可点击；点击后 `go_case_list(suite_id)` + `st.rerun()`
- [x] 6.4 操作栏三按钮：进入（→`go_case_list`）/ 修改（→ 弹对话框）/ 删除（→ 二次确认 + 调 `delete_suite_with_confirm`）
- [x] 6.5 删除按钮 `disabled` 条件：`case_count > 0` 时禁用，`help` 提示「套件内还有 N 条用例，请先删除」

## 7. UI — 套件新增 / 修改对话框

- [x] 7.1 新增 `@st.dialog("新增套件")` 函数 `show_create_suite_dialog()`：表单字段「系统名称」「版本号」，「创建人」只读展示 `get_current_user()`；保存按钮调 `suite_service.create_suite`，捕获 `SuiteDuplicateError` 提示
- [x] 7.2 新增 `@st.dialog("修改套件")` 函数 `show_edit_suite_dialog(suite_id)`：表单预填当前 name/version；保存调 `suite_service.update_suite`，冲突提示
- [x] 7.3 在套件列表页点击「新增」时 `st.session_state.tc_suite_dialog = "create"` + `st.rerun()`，渲染前判断
- [x] 7.4 在套件列表页点击「修改」时 `st.session_state.tc_suite_dialog = "edit"` 且 `tc_suite_editing_id = suite_id` + `st.rerun()`

## 8. UI — 用例列表页改造

- [x] 8.1 在 `render_list_view()` 顶部用 `go_suite_list()` 返回按钮 + 面包屑：`套件 / {suite.name} {suite.version}`
- [x] 8.2 标题改为 `f"测试用例 — {suite.name}"`；用 `list_testcases(suite_id=tc_active_suite_id)` 过滤
- [x] 8.3 录制完成自动创建用例的路径（`page_testcases.py` 末尾）传 `suite_id=tc_active_suite_id` 给 `create_testcase`

## 9. 验证

- [x] 9.1 启动 Streamlit 应用，确认 `logs/suites.json` 自动创建，「默认系统」套件自动出现且 `case_count` 等于历史用例数
- [x] 9.2 在套件列表点击「+ 新增」→ 输入「电商后台 / v1.0」→ 保存 → 列表新增一行；重复提交同名同版本应失败
- [x] 9.3 点击「电商后台」的「系统名称」/「进入」→ 进入空用例列表；返回套件列表
- [x] 9.4 点击「修改」→ 改名「电商后台2」+ 改版本「v2.0」→ 列表行更新且「上次操作时间」变化
- [x] 9.5 「电商后台2」删除按钮可点（case_count=0）→ 二次确认 → 删除成功
- [x] 9.6 「默认系统」删除按钮置灰（case_count>0），鼠标悬停显示 N 条用例提示
- [x] 9.7 在「默认系统」下录制一条新用例 → 返回套件列表 → 「默认系统」的「上次操作时间」已刷新
- [x] 9.8 关闭并重启应用 → 「默认系统」未重复创建；用例未丢
- [x] 9.9 既有回放能力（`streamlit-app-testcase-playback`）回归：列表展开 / 详情页 / ▶ 回放 / 历史展示均正常
