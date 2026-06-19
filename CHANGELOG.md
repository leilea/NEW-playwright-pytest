# Changelog

## v0.1.0 (2026-06-19)

**初始版本 — Playwright+Pytest 测试平台基础框架**

### Features

- 测试套件管理（CRUD + 版本号）
- 测试用例管理（操作步骤编辑器）
- Playwright 录制（JS 注入模式，支持 click/fill/goto 等 12 种动作）
- 脚本生成器（已录制步骤 → pytest 脚本）
- 回放执行（浏览器 headed 模式，实时结果输出）
- 用户认证（JWT 登录）

### Fixes

- script_gen.py: 兼容展平与嵌套两种步骤格式
- script_gen.py: 中文用例名 sanitize（isascii 过滤防乱码）
- script_gen.py: 补充 uncheck 动作 handler
- step.ts: 补充 uncheck 类型定义
- rec_ws.py: 改用 recorder_process.py（Mode B）替代 codegen CLI
- rec_ws.py: Windows 子进程兼容（Popen + run_in_executor）
- recorder_process.py: JS 注入改用 add_init_script（每次页面加载自动注入）
- 录制结束竞态条件修复（等待子进程排出事件再关闭）
- playback.py: 兼容 Windows subprocess + 临时文件写入系统 TEMP
- CaseEditor.vue: 三页签布局重构

### Commits

- `576e93f` feat(case-editor): tabs layout, playback headed, script gen ascii sanitize
- `4619575` fix(script-gen): accept flat step format alongside nested params
- `81afa8c` fix(build): resolve TypeScript strict build errors
