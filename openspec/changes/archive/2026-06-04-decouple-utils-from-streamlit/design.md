## 上下文

**当前状态**：
- `streamlit_app/utils/allure_reader.py:6` 直接 `import streamlit as st`
- `streamlit_app/utils/allure_reader.py:37-48` 用 `@st.cache_data(ttl=10)` 装饰 `get_summary`
- utils 层其他文件 (`config_manager` / `testcase_store` / `suite_store` / `playback_history` / `report_cache` / `test_executor`) **已经全部是纯 Python**，不依赖任何 UI 框架

**约束**：
- 不修改 `tests/`、`conftest.py`、`pytest.ini`
- 不引入新依赖
- 行为完全等价：相同入参 → 相同返回，10 秒 TTL 重新计算
- 不改 `page_dashboard.py` 等调用方的代码

**利益相关者**：维护者（希望 utils 真正变成可复用的纯工具层）、未来前端迁移方（不希望 utils 绑死 streamlit）

## 目标 / 非目标

**目标**：
- allure_reader 不再 import streamlit
- 提供 1 个项目内部的 TTL 缓存工具（`utils/cache.py`）
- 行为完全等价

**非目标**：
- 不重写 allure_reader 的业务逻辑（JSON 解析、Pandas 分组、metrics 计算等保持原样）
- 不引入第三方缓存库（如 `cachetools`）
- 不改其他 utils 文件（已经是纯 Python）
- 不改 `page_dashboard.py` 等调用方

## 决策

### 决策 1：自实现 `ttl_cache`，不引入第三方库

**采用**：在 `utils/cache.py` 写一个约 30 行的 `ttl_cache(ttl_seconds)` 装饰器，底层用 `functools.wraps` + `time.monotonic()` + 实例级 dict 存 (timestamp, value)。

**理由**：
- 引入 `cachetools` 仅为 1 个 TTL 装饰器不值得（依赖污染）
- `functools.lru_cache` 不带 TTL，强行用需要额外 hack
- Streamlit 的 `@st.cache_data` 内部就是类似的实现，自实现可读性高

**替代方案**：
- ❌ `cachetools.TTLCache`：依赖 +20KB，且与"保持轻量"的项目惯例不符
- ❌ `functools.lru_cache(maxsize=128)`：无 TTL，缓存永不失效，与原行为 10s TTL 不等价

### 决策 2：装饰器签名与 `@st.cache_data` 保持最小兼容

**采用**：`@ttl_cache(ttl_seconds=10)`，仅 1 个参数。

**理由**：
- allure_reader 的现有调用是 `@st.cache_data(ttl=10)`，等价替换为 `@ttl_cache(ttl_seconds=10)` 即可
- 未来其他 utils 也能用，签名简单

**替代方案**：
- ❌ `lru_cache(maxsize=...)` + `typed=...` 完整参数透传：现阶段没有调用方需要这些参数，先 YAGNI

### 决策 3：装饰器状态用闭包字典，不放类

**采用**：
```python
def ttl_cache(ttl_seconds: int):
    state = {}  # 单个被装饰函数一个闭包
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            cached = state.get(key)
            if cached is not None:
                ts, value = cached
                if now - ts < ttl_seconds:
                    return value
            value = fn(*args, **kwargs)
            state[key] = (now, value)
            return value
        return wrapper
    return decorator
```

**理由**：
- 闭包作用域天然隔离每个被装饰函数的缓存
- 不需要类 / `WeakValueDictionary` 等额外复杂度
- 单用户本地工具，无并发问题（Streamlit 单进程）

**替代方案**：
- ❌ 全局 dict 索引：需要手动清空，不优雅
- ❌ 锁：单进程单线程，引入锁是 over-engineering

## 风险 / 权衡

- **[风险] ttl 闭包持有函数返回值，无法被 GC** → 缓解：原 `@st.cache_data` 也有同样问题；这是缓存的固有 trade-off；allure_reader 缓存量小（最多 ~100 个 pytest 报告），可忽略
- **[风险] 浮点时间精度** → 缓解：用 `time.monotonic()` 不受系统时间调整影响；TTL 比较用 `<` 而非 `<=`，与原行为一致
- **[权衡] 失去 Streamlit `cache_data` 的磁盘溢出与跨进程共享能力** → 接受：allure_reader 不需要这些；纯内存缓存对 ~100 个报告足够

## 迁移计划

无破坏性变更：

1. 新增 `streamlit_app/utils/cache.py`
2. 修改 `streamlit_app/utils/allure_reader.py`：
   - 删 `import streamlit as st`
   - 删 `@st.cache_data(ttl=10)`
   - 加 `from streamlit_app.utils.cache import ttl_cache`
   - 改 `@ttl_cache(ttl_seconds=10)`
3. 启动 streamlit，`page_dashboard` 渲染 dashboard；get_summary 返回值与原完全一致

**回滚策略**：单文件 git revert 即可恢复 allure_reader 原状；新文件 `utils/cache.py` 可保留（无副作用）

## 开放问题

无
