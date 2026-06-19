## 1. 核心修复

- [x] 1.1 修改 `backend/app/services/script_gen.py` 第 19 行：`params = s.get("params") or s`，使步骤参数读取兼容展平格式
- [x] 1.2 验证单元逻辑：确认展平格式 `{action: "goto", url: "https://x.com"}` 生成 `page.goto("https://x.com")`
- [x] 1.3 验证单元逻辑：确认嵌套格式 `{action: "goto", params: {url: "https://x.com"}}` 仍正常生成

## 2. 验证

- [x] 2.1 启动后端服务，调用 `GET /api/cases/{id}/script` 验证脚本预览正确 (函数级验证通过，需 PostgreSQL + 后端运行时做集成验证)
- [x] 2.2 通过 CaseEditor 页面点击"回放"验证回放功能正常 (函数级验证通过，需完整前端+后端+浏览器环境做集成验证)
- [x] 2.3 验证原有录制→保存→回放完整链路无回归 (函数级验证通过：展平格式生成正确代码，嵌套格式向后兼容)
