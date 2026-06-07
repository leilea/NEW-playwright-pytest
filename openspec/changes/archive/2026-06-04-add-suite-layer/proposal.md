## 为什么

当前 `streamlit_app` 的「测试用例」页面是**平铺展示**——所有用例直接列在 `testcases.json` 一个 JSON 数组里。随着 QA 团队逐步接入多条业务线（电商后台、CRM、运营平台……），用例的"业务归属"信息缺失，表现为：

- 无法按"系统 / 产品"维度管理用例
- 删除 / 改一个套件下的脚本时无法收敛范围
- 录制好的脚本没有"属于哪个系统"的元数据，回放失败后排查时只能靠记忆

因此需要**在测试用例之上再加一层「套件（系统）」容器**，把用例按"系统名称 + 版本号"组织起来。

## 变更内容

为 Streamlit 用例管理页面新增 **套件（Suite）层**，形成两级导航：

- **新增** `streamlit_app/utils/suite_store.py`：套件持久化层
- **新增** `streamlit_app/services/suite_service.py`：套件业务逻辑（含启动期「默认系统」迁移）
- **新增** `streamlit_app/controllers/suite_controller.py`：套件编排（带用例数量的列表加载）
- **新增** 规范 `streamlit-app-testcase-suite`：套件的接口 / 数据契约
- **扩展** `streamlit_app/utils/testcase_store.py`：每条用例新增 `suite_id` 字段；启动时把无 `suite_id` 的历史用例自动归入「默认系统」套件
- **扩展** `streamlit_app/utils/config_manager.py`：新增 `get_current_user()`，读取 `USER` / `USERNAME` 环境变量
- **扩展** `streamlit_app/services/testcase_service.py`：`list_testcases` 接受可选 `suite_id`；`create_testcase` / `update_testcase` / `delete_testcase` 操作后回写所属套件 `updated_at`
- **修改** `streamlit_app/page_testcases.py`：扩展 `tc_view` 状态机，新增 `render_suite_list_view()` 套件列表页与套件「新增 / 修改」对话框

**不涉及**：
- 不修改 `tests/`、`conftest.py`、`pytest.ini`
- 不修改 `streamlit-app-testcase-playback` 既有契约（仅被 `tc_view` 状态机外层包住）
- 不引入新依赖
- 不做套件导入 / 导出
- 不修先前报告的既有 bug（保持单一职责）

## 功能 (Capabilities)

### 新增功能
- `streamlit-app-testcase-suite`: 套件层能力 —— 套件 CRUD、套件下用例归属、启动期历史数据迁移、套件删除前置校验、套件维度用例数量统计

### 修改功能
- 无（既有用例 CRUD 契约不变，仅 `list_testcases` 新增可选 `suite_id` 参数，向后兼容）

## 影响

- **代码**：`streamlit_app/` 子树新增 3 文件 + 修改 4 文件
- **数据**：
  - 新增 `logs/suites.json`（启动时自动创建）
  - `testcases.json` 全部条目新增 `suite_id` 字段（启动时一次性迁移，幂等）
- **运行时**：无新依赖；UI 状态机扩展 1 个 view、3 个 session_state 键
- **测试代码**：无影响
- **用户可见行为**：
  - 打开「测试用例」页默认显示**套件列表**（不是用例列表）
  - 套件下用例数 = 0 时删除按钮可点；> 0 时置灰
  - 套件 `updated_at` = 套件自身或子用例最后一次变更的时间
