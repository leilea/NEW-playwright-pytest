## 1. 工具模块

- [x] 1.1 创建 `streamlit_app/utils/cache.py`：实现 `ttl_cache(ttl_seconds: int)` 装饰器，内部用闭包 + `time.monotonic()` + dict 实现 TTL 缓存；保留 `functools.wraps` 签名

## 2. 替换 allure_reader 中的 streamlit 依赖

- [x] 2.1 修改 `streamlit_app/utils/allure_reader.py`：删除 `import streamlit as st`
- [x] 2.2 修改 `streamlit_app/utils/allure_reader.py`：`get_summary` 装饰器从 `@st.cache_data(ttl=10)` 改为 `@ttl_cache(ttl_seconds=10)`，import 来源改为 `streamlit_app.utils.cache`

## 3. 验证

- [x] 3.1 运行 `python -c "import ast, sys; from pathlib import Path; sys.path.insert(0, '.'); from streamlit_app.utils import allure_reader; print('OK')"` 确认模块可被无 streamlit 上下文的脚本 import
- [x] 3.2 用 `grep -rn "import streamlit" streamlit_app/utils/` 确认无任何 UI 框架导入残留
- [x] 3.3 启动 streamlit，进入「仪表盘」页面，确认 dashboard 正常渲染（get_summary 返回值与原一致）
