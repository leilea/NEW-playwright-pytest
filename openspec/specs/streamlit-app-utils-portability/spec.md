# streamlit-app-utils-portability 规范

## 目的
待定 - 由归档变更 decouple-utils-from-streamlit 创建。归档后请更新目的。
## 需求
### 需求:utils 模块禁止依赖 UI 框架

`streamlit_app/utils/` 下的所有 Python 模块必须不 `import` 任何 UI 框架（`streamlit` / `flask` / `fastapi` / `django` / `pyramid` 等），也不得使用这些框架专属的全局对象（如 `st.session_state`、`@st.cache_data` / `@app.route` / `@flask_*.route`）。

#### 场景:utils 模块中无 UI 框架导入
- **当** 扫描 `streamlit_app/utils/**/*.py` 所有模块
- **那么** 必须没有任何 `import streamlit` / `import flask` / `import fastapi` 等 UI 框架导入语句
- **并且** 不得使用 `@st.cache_data` / `@st.cache_resource` / `@app.route` 等装饰器

#### 场景:utils 模块提供框架无关的缓存原语
- **当** utils 模块需要 TTL 缓存
- **那么** 必须使用项目自实现的 `streamlit_app.utils.cache.ttl_cache` 装饰器，不得引用任何 UI 框架的缓存装饰器

#### 场景:utils 模块可被非 streamlit 调用方复用
- **当** 一个 Python 脚本（非 streamlit 上下文）import `streamlit_app.utils.allure_reader` 并调用其函数
- **那么** 该调用不得要求 streamlit 运行时（即 `import streamlit` 不得发生）

