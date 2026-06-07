## 上下文

- **当前状态**：`streamlit_app/services/testcase_service.py` 提供用例 CRUD，`logs/testcases.json` 持久化为**平铺数组**；`streamlit_app/page_testcases.py` 进入「测试用例」页时直接渲染所有用例。`streamlit-app-testcase-playback` 规范已定义了回放能力，本次新加套件层**不动其契约**。
- **约束**：
  - 不修改 `tests/`、`conftest.py`、`pytest.ini`
  - 不引入新依赖
  - 历史 `testcases.json` 中**可能已存若干无 `suite_id` 的用例** —— 启动必须幂等迁移，不允许数据丢失
  - 套件下用例数 > 0 时**禁止删除**（UI 禁用 + 后端校验）
- **利益相关者**：QA 工程师（核心用户：按业务线管理用例）、平台维护者（不希望回归既有回放 / 录制能力）

## 目标 / 非目标

**目标**：
- 在 UI 中实现"套件列表 → 用例列表"两级导航
- 套件数据（`name` + `version`）组合唯一
- 套件 `updated_at` 自动反映最后一次"该套件或其下用例"的变更
- 启动时一次性把无主用例归入「默认系统 / v1.0」
- 删除非空套件被禁止（双重防护）

**非目标**：
- 不做套件导入 / 导出
- 不做套件树 / 多级嵌套（套件是平铺一层）
- 不做套件权限 / 多租户
- 不修先前报告的 5 个既有 bug
- 不修改 `streamlit-app-testcase-playback` 既有契约

## 决策

### 决策 1：套件与用例分离存储，suite_id 外键引用

**采用**：新建 `logs/suites.json`（`{"suites": [...]}`），用例 `testcases.json` 每条新增 `suite_id` 字段。

**理由**：
- 与现有 `testcases.json` / `playback_history.json` 风格一致，人类可读
- 套件维度查询（"哪些套件存在？"）是 O(1) 文件读；用例数通过 `suite_id` 字段 O(n) 聚合即可（n 量级 < 1k）
- 外键引用避免"套件数据冗余拷贝到每条用例"

**替代方案**：
- ❌ 嵌套结构（每条用例内嵌套件信息）：更新套件名时需要遍历所有用例改写，O(n) 写
- ❌ SQLite：与项目"轻量 JSON 文件"惯例不符，引入新依赖

### 决策 2：启动期一次性迁移到「默认系统」

**采用**：`testcase_store._ensure_store()` 之后调用 `_migrate_default_suite()`，扫描 `testcases` 中无 `suite_id` 的条目：
1. 若 `suites.json` 无 `name == "默认系统"` 套件 → 创建一个（`version="v1.0"`、`created_by=get_current_user()`）
2. 把所有孤儿用例的 `suite_id` 写为该套件 `id`
3. 原子写回 `testcases.json`

**理由**：
- 启动期一次性写回 + 幂等，下次启动 `orphan_count == 0` 直接跳过
- 不需要单独跑 migration 脚本，部署即生效
- 「默认系统」作为兜底套件，UI 上**不特殊标记**，与其他套件平等展示

**替代方案**：
- ❌ 运行时懒迁移（读时才补 `suite_id`）：N 次读 = N 次扫描，复杂度高
- ❌ 标记为「未分组」灰色态：增加 UI 复杂度，干扰正常使用

### 决策 3：套件下用例操作回写 updated_at

**采用**：在 `testcase_service.create_testcase` / `update_testcase` / `delete_testcase` 末尾，调用 `_touch_suite(suite_id)` —— 把该套件 `updated_at` 写为 `now()`。

**理由**：
- 套件列表的「上次操作时间」要忠实反映"该套件最近活跃时刻"，最直观定义就是"该套件或其下用例最后一次变更"
- 集中在服务层，UI 无需感知

**替代方案**：
- ❌ UI 层每次操作后手写：易遗漏，且违反"业务逻辑收敛在服务层"的项目惯例
- ❌ 单独字段 `last_case_op_at`：与 `updated_at` 重复，且需额外维护一致性

### 决策 4：组合唯一（name + version）— UI 校验 + 后端校验

**采用**：
- 新增套件时 `create_suite` 后端先查 `name + version` 是否已存在，存在则 `raise SuiteDuplicateError`
- UI 弹错提示「该系统名称 + 版本号的套件已存在」

**理由**：
- 业务上"同名同版本"无意义（容易混淆）
- 双层校验符合项目惯例（参考 `delete_suite_if_empty` 的双层防护）

### 决策 5：删除非空套件 — UI 禁用 + 后端 raise

**采用**：
- `suite_service.delete_suite_if_empty(suite_id)`：
  - `count == 0` → 删除，返回 `(True, "")`
  - `count > 0` → 返回 `(False, "套件内还有 N 条用例，请先删除")`
- UI 列表行 `用例数 > 0` 时把删除按钮 `disabled=True` + `help="..."` 提示

**理由**：
- 防止用户误删导致"幽灵用例"（`suite_id` 指向不存在的套件）
- `disabled` 按钮对鼠标悬停用户友好；后端兜底防止绕过 UI

### 决策 6：UI 用 `st.dataframe` 套件列表 + `st.dialog` 套件表单

**采用**：
- 套件列表用 `st.dataframe` + 按钮列外置（参考 `page_reports.py` 的 `st.dataframe` 风格）
- 套件「新增」「修改」用 `@st.dialog`（参考 `show_create_dialog`）
- 「系统名称」点击触发进入 → 用 `st.button(..., type="tertiary")` 模拟链接样式

**理由**：
- 与项目既有 UI 风格统一
- `st.dialog` 阻塞性强但适合"必须先填完才能继续"的表单
- 系统名称作为可点击元素符合"列表→详情"的直觉

### 决策 7：状态机扩展最小化

**采用**：`tc_view` 状态值扩展 1 个 `"suite_list"`（默认入口）；新增 3 个 session_state 键：
- `tc_active_suite_id: Optional[str]` —— 当前进入的套件
- `tc_suite_dialog: Optional[str]` —— `"create"` / `"edit"` / `None`
- `tc_suite_editing_id: Optional[str]` —— 编辑中的套件 id

**理由**：
- 复用既有 `tc_view` 枚举值，状态机扩展面最小
- 既有 `"case_list"` / `"case_detail"` / `"case_recording"` 行为不变，仅多一层入参 `suite_id`

**替代方案**：
- ❌ 拆成两个独立页面（`page_suites.py` + `page_testcases.py`）：Streamlit 多页应用下难以在页面内做"进入"导航，必须用 `st.switch_page`，交互割裂

## 风险 / 权衡

- **[风险] 历史 `testcases.json` 损坏** → 缓解：`json.load` 异常时 `_ensure_store` 重新初始化为 `{"testcases": []}`，迁移函数捕获异常
- **[风险] 并发修改 `testcases.json` + `suites.json`** → 缓解：保留项目惯例，**不加锁**（单用户本地工具）；`save` 用临时文件 + `os.replace` 原子写
- **[风险] `_touch_suite` 失败但用例已保存** → 缓解：先做 `save(tc)`，再 `_touch_suite`；即使 touch 失败也不影响用例一致性，只损失时间戳精度
- **[风险] 套件名称超长 / 含特殊字符** → 缓解：UI `text_input` 不限长度但 `max_chars=64`；后端不做字符校验，留给产品决定
- **[权衡] `st.dataframe` 列表中的「操作」列不能用交互控件** → 接受：在 dataframe 外用 `st.columns` 把每行的"进入 / 修改 / 删除"按钮拉出来单独渲染（与既有 `render_list_view` 的 `st.container(border=True)` 卡片风格保持一致）
- **[权衡] `_touch_suite` 每次用例 CRUD 都触发一次文件读改写** → 接受：单用户场景下 I/O 可忽略；如未来高并发可加内存缓存

## 迁移计划

无破坏性变更，**不需手动迁移**：

1. 部署后首次启动 → `_ensure_store()` 创建 `suites.json`（空数组）→ `_migrate_default_suite()` 扫到孤儿用例 → 创建「默认系统」→ 原子写回
2. 第二次启动 → 孤儿计数 = 0 → 迁移直接跳过
3. 既有 `streamlit-app-testcase-playback` 行为**完全不变**（用例脚本字段未动；`list_testcases` 新增可选参数）

**回滚策略**：删除 `logs/suites.json` + 清理 `testcases.json` 中所有 `suite_id` 字段（恢复成平铺）。因为 `_migrate_default_suite` 幂等，**前向兼容** —— 回滚后再次部署会自动重新迁移。

## 开放问题

- 无（与用户确认所有关键决策）
