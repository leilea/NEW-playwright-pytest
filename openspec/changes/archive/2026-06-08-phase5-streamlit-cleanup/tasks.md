## 1. 归档文档

- [x] 1.1 创建 `docs/superpowers/historical/streamlit-app-deprecated.md` 归档记录

## 2. 删除 Streamlit 运行时文件

- [x] 2.1 `git rm -r streamlit_app/` 删除整个目录
- [x] 2.2 `git rm -rf .streamlit/` 删除配置目录
- [x] 2.3 删除 `Dockerfile.txt`（已由 docker-compose.yml + backend/Dockerfile 替代）
- [x] 2.4 删除 `streamlit_smoke.log` 和 `logs/streamlit_stdout.log`、`logs/streamlit_stderr.log`

## 3. 清理依赖与配置文件

- [x] 3.1 修改 `requirements.txt` 移除 `streamlit`、`streamlit-authenticator`、`streamlit-extras`
- [x] 3.2 修改 `AGENTS.md` 移除 Streamlit 引用（第 61 行）

## 4. 修复外部引用

- [x] 4.1 修复 `backend/tests/integration/test_dual_write.py` 的 import 路径
- [x] 4.2 更新 `backend/scripts/check_migration_readiness.py` 移除 streamlit 存在性检查

## 5. 清理遗留数据与 pycache

- [x] 5.1 `git rm -r streamlit_app/` 已连带清理所有 `__pycache__` 文件
- [x] 5.2 删除 `logs/suites.json`、`logs/testcases.json`、`logs/playback_history.json` 遗留 JSON 存储
