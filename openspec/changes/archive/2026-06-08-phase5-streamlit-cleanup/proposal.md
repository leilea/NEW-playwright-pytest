## 为什么

Streamlit→Vue/TS 迁移已完成（38 任务全部提交），但 Phase 5 的实际清理动作尚未执行。`streamlit_app/` 目录、`.streamlit/` 配置、Streamlit 依赖等残留文件仍在仓库中，对新开发者造成困惑，也增加了维护负担。

## 变更内容

执行 Phase 5 收尾清理：

- 删除 `streamlit_app/` 整个目录
- 删除 `.streamlit/` 配置目录
- 清理 `requirements.txt`（移除 streamlit 及相关依赖）
- 归档/删除已废弃的 `Dockerfile.txt`
- 删除遗留的 JSON 存储文件（`logs/suites.json`, `logs/testcases.json`）
- 创建归档记录 `docs/superpowers/historical/streamlit-app-deprecated.md`
- 清理所有 streamlit 相关引用（AGENTS.md、日志文件、测试引用）

## 功能 (Capabilities)

### 新增功能

无。这是纯粹的清理操作，不引入新功能。

### 修改功能

无。行为无变化。

## 影响

- **删除**: `streamlit_app/`, `.streamlit/`, `Dockerfile.txt`
- **修改**: `requirements.txt`, `AGENTS.md`
- **清理**: 日志文件、遗留 JSON 存储、pycache
