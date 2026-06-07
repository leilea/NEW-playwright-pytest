## 上下文

**当前状态**：
- `streamlit_app/page_testcases.py:57-82` 用 12 个独立的 `if "tc_*" not in st.session_state: st.session_state.tc_* = <default>` 块做初始化
- `tc_view` 是裸字符串 `"suite_list" | "case_list" | "detail" | "recording"`，定义散落在 `go_suite_list()` / `go_case_list()` / `go_recording()` / `go_detail()` 4 个跳转函数里
- 12 个 `tc_*` 键的类型仅靠注释与初始化值隐式表达，没有任何类型签名

**约束**：
- 不修改 `tests/`、`conftest.py`、`pytest.ini`
- 不引入新依赖（`enum` 与 `TypedDict` 均为标准库）
- 12 个字段名必须保持不变（业务代码大量使用 `st.session_state.tc_active_suite_id` 等）
- 行为完全不变

**利益相关者**：维护者（希望 page_testcases.py 这种 580+ 行的最复杂页面有类型安全）、未来迁移方（希望状态机 1:1 平移到 Pinia store）

## 目标 / 非目标

**目标**：
- 把 4 个视图值显式化为 `TestcaseView` 枚举
- 把 12 个会话字段显式化为 `TestcaseSessionState` TypedDict
- 提供 `DEFAULT_TESTCASE_SESSION_STATE()` 工厂函数收口初始化逻辑
- 行为完全等价

**非目标**：
- 不把状态机迁移到外部库（如 `streamlit-state-machine`）
- 不改 4 个跳转函数 `go_*` 的名称
- 不改任何业务逻辑（删除用例、回放面板、录制流程等）
- 不动 `page_dashboard.py` / `page_runner.py` / `page_reports.py` / `page_config.py`

## 决策

### 决策 1：枚举与 TypedDict 放新文件 `streamlit_app/types/testcase_state.py`

**采用**：新建 `streamlit_app/types/` 目录，存放跨页面共享的类型定义。

**理由**：
- 现有 `streamlit_app/utils/` / `services/` / `controllers/` 都不适合放纯类型（utils 是运行时函数，services 是业务，controllers 是编排）
- `types/` 是新层，但只放 1 个文件，零维护负担
- 后期如果其他页面需要类似状态机（如 `page_runner` 的运行状态），可复用 `types/` 模式

**替代方案**：
- ❌ 放 `utils/`：utils 命名暗示"工具函数"，放 TypedDict 与 enum 不合适
- ❌ 放 `page_testcases.py` 顶部：失去"跨页面共享"语义

### 决策 2：`TestcaseView` 用 `str, Enum` 混合继承

**采用**：
```python
class TestcaseView(str, Enum):
    SUITE_LIST = "suite_list"
    CASE_LIST = "case_list"
    DETAIL = "detail"
    RECORDING = "recording"
```

**理由**：
- 继承 `str` 让 `TestcaseView.SUITE_LIST == "suite_list"` 仍为 True，业务代码用 `st.session_state.tc_view = "case_list"` 这种字符串赋值也仍能工作（向下兼容）
- 继承 `Enum` 让 IDE 与 mypy 能识别合法值

**替代方案**：
- ❌ 纯 `Enum`：`st.session_state.tc_view` 存的是字符串，比较时会失败，需批量改业务代码
- ❌ `Literal["suite_list", "case_list", "detail", "recording"]`：不能用作类型提示的主语（无 docstring 空间）

### 决策 3：TypedDict 严格保持原字段名

**采用**：12 个字段名一字不改（`tc_view` / `tc_active_suite_id` / `tc_suite_dialog` / `tc_suite_editing_id` / `tc_editing_id` / `tc_detail_id` / `tc_show_dialog` / `tc_auto_created` / `tc_recording` / `tc_playback_running` / `tc_playback_handle` / `tc_playback_logs` / `tc_playback_result`）。

**理由**：
- 业务代码 580 行中大量引用这些字段名，改名 = 全文件重写
- session_state key 是 Streamlit 持久化层（用户浏览器 session 内存），改名后用户行为会被重置
- 保持原名 = 零迁移成本

### 决策 4：提供工厂函数而非模块级常量

**采用**：
```python
def DEFAULT_TESTCASE_SESSION_STATE() -> TestcaseSessionState:
    return {
        "tc_view": TestcaseView.SUITE_LIST,
        "tc_recording": None,
        ...
    }
```

**理由**：
- 返回新 dict，避免可变默认值陷阱
- 调用方：`for k, v in DEFAULT_TESTCASE_SESSION_STATE().items(): if k not in st.session_state: st.session_state[k] = v`

**替代方案**：
- ❌ 模块级 `_DEFAULT = {...}`：可变共享状态，streamlit 跨用户会串味
- ❌ `dataclass`：TypedDict 已够用；dataclass 强制实例化，与 session_state 字典交互不优雅

## 风险 / 权衡

- **[风险] 字段遗漏** → 缓解：迁移时 12 个字段一一比对原 `if ... not in st.session_state` 块；每加 1 个字段在 PR review 时强制看 streamlit 实际行为是否破坏
- **[风险] `TypedDict` 在 Python 3.7 之前不可用** → 缓解：项目 `requirements.txt` 与 `pytest` 配置隐含 Python 3.8+；最低支持版本已在 Streamlit 1.x 要求之上
- **[权衡] `tc_suite_dialog: Literal[...]` 字段声明 `Optional[Literal[...]]` 不直观** → 接受：用 `Optional[Literal["create", "edit"]]` 表达"None 或 2 选 1"，Python 类型系统无更精确表达

## 迁移计划

无破坏性变更：

1. 新增 `streamlit_app/types/__init__.py`（空）+ `streamlit_app/types/testcase_state.py`
2. 修改 `streamlit_app/page_testcases.py`：
   - 12 个 `if ... not in st.session_state` 块替换为 1 个 `_init_session_state()` 函数
   - `go_suite_list()` / `go_case_list()` / `go_recording()` / `go_detail()` 内对 `tc_view` 的字符串赋值改为 `TestcaseView.*` 枚举
3. 启动 streamlit，逐个 view 切换验证

**回滚策略**：单文件 revert；新目录 `types/` 保留无副作用

## 开放问题

无
