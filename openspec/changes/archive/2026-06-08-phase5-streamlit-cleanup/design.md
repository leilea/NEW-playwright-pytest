## 上下文

迁移计划 38 个任务已全部提交，但 Phase 5 的清理步骤未实际执行。`streamlit_app/` 目录（含 7+ 页面、services/、controllers/、utils/、assets/）和 `.streamlit/config.toml` 仍在仓库中。

此外 `backend/tests/integration/test_dual_write.py` 仍从 `streamlit_app.services.pg_writer` 导入，`AGENTS.md` 仍引用 `streamlit_app/`，日志文件残留。

## 目标 / 非目标

**目标：**
- 删除所有 Streamlit 运行时文件（`streamlit_app/`、`.streamlit/`）
- 清理依赖项（`requirements.txt` 移除 streamlit 相关）
- 归档遗留文档（`docs/superpowers/historical/streamlit-app-deprecated.md`）
- 更新所有引用（AGENTS.md、测试导入、检查脚本）
- 清理日志和 pycache 文件

**非目标：**
- 不修改 Vue 前端或 FastAPI 后端代码
- 不修改运行时行为
- 不删除 OpenSpec 规范/归档（历史记录保留）

## 决策

1. **直接删除 vs 备份 → 再删除**: 执行 `git rm -r streamlit_app/` 而非直接文件删除，确保 Git 追踪。完整历史可在 `git log -- streamlit_app/` 找回，无需额外备份。
2. **测试导入处理**: `backend/tests/integration/test_dual_write.py` 导入的 `pg_writer` 无实际 Streamlit 依赖，将其移至 `backend/app/services/pg_writer.py` 避免断链。
3. **`check_migration_readiness.py` 更新**: 保留脚本但移除其对 `streamlit_app` 存在的检查。
4. **pycache**: 通过 `git rm -r --cached` 清理，不纳入 `.gitignore`（避免影响未来 pycache 策略）。

## 风险 / 权衡

- **风险**: 测试 `test_dual_write.py` 可能因 import 路径变化而失败 → 修复 import 路径
- **风险**: 有人仍在本地使用 Streamlit → 已过 30 天观察期，可安全删除
- **权衡**: 保留 `docs/superpowers/specs/` 和 `openspec/specs/` 中的历史 Streamlit 规范作为参考
