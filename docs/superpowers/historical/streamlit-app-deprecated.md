# Streamlit 应用 — 已弃用归档

> **弃用日期：** 2026-06-08
> **替代方案：** Vue 3 + FastAPI 前后端分离架构
> **迁移计划：** `docs/superpowers/plans/2026-06-07-streamlit-to-vue-migration.md`
> **迁移规格：** `docs/superpowers/specs/2026-06-07-streamlit-to-vue-migration-design.md`

## 历史

Streamlit 单体应用曾是 `NEW-playwright-pytest-main` 的主要 UI，提供 5 个页面（仪表盘、测试运行、测试用例、报告、系统配置），通过 Streamlit 的 session state 管理状态，JSON 文件做持久化。

## 删除内容

- `streamlit_app/` — 全部代码（5 页面、controllers、services、utils、types、assets）
- `.streamlit/config.toml` — Streamlit 框架配置
- `requirements.txt` 中的 `streamlit` 系列依赖
- 遗留的 JSON 存储文件（`logs/suites.json`、`logs/testcases.json`）

## Git 历史查看

```bash
git log -- streamlit_app/
```

## 替代方案

| 功能 | Streamlit | Vue + FastAPI |
|------|-----------|---------------|
| 仪表盘 | `page_dashboard.py` | `Dashboard.vue` + `/api/dashboard` |
| 测试运行 | `page_runner.py` | `Runs.vue` + `/api/runs` + WS |
| 测试用例 | `page_testcases.py` | `CaseEditor.vue` + `StepEditor` + `Recorder` |
| 报告 | `page_reports.py` | `Reports.vue` + `/api/reports` |
| 系统配置 | `page_config.py` | `Config.vue` + `/api/config` |
| 持久化 | JSON 文件 | PostgreSQL + SQLAlchemy |
| 实时推流 | Streamlit 轮询 | WebSocket |
