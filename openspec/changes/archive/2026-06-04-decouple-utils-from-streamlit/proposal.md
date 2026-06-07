## 为什么

`streamlit_app/utils/allure_reader.py` 在 utils 层直接 `import streamlit as st` 并用 `@st.cache_data` 装饰函数（line 6, line 37），违反了项目既有的分层约定（utils/ 应是纯 Python、与 UI 框架无关）。这个泄漏让 utils 无法被 CLI、测试脚本、或未来的非 Streamlit 前端复用。

本次变更只动 1 个文件 + 新增 1 个工具模块，不改任何业务行为。

## 变更内容

- **新增** `streamlit_app/utils/cache.py`：通用 TTL 缓存工具，提供与 `@st.cache_data(ttl=N)` 等价的接口（`ttl_cache(ttl_seconds)` 装饰器）
- **修改** `streamlit_app/utils/allure_reader.py`：
  - 移除 `import streamlit as st` 与 `@st.cache_data` 装饰器
  - 改用 `utils/cache.py` 的 `ttl_cache` 装饰器
  - 行为完全不变：相同入参 → 相同返回，TTL 到期后重新计算
- **不修改** `streamlit_app/app.py` 与所有 `page_*.py` —— 它们仍可正常调用 allure_reader，cache 装饰器对调用方透明

## 功能 (Capabilities)

### 新增功能
- `streamlit-app-utils-portability`: utils 层与 UI 框架解耦 —— utils 模块必须不依赖任何前端框架（streamlit / flask / fastapi 等），不得使用框架专属的装饰器与全局对象。

### 修改功能
- 无（既有用例 / 套件 / 回放 3 个能力的需求不变，仅 allure_reader 内部实现替换）

## 影响

- **代码**：`streamlit_app/utils/` 改动 1 个文件 + 新增 1 个文件（~30 行）
- **运行时**：零依赖新增；行为完全等价
- **测试代码**：无影响
- **用户可见行为**：无变化
- **可回滚**：utils/cache.py 是新模块、allure_reader.py 改动收敛在一文件，单 git revert 即可恢复
