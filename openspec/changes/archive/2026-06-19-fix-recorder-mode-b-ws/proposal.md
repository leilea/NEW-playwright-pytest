## 为什么

录制功能完全不可用——点击"开始录制"立即提示"录制错误"。根因是 `rec_ws.py` 使用了废弃的 Mode A（`playwright codegen` CLI 子进程），该方案不稳定且不实时流式输出步骤。Mode B（`recorder_process.py`）已实现但未接入 WebSocket。此外 `recorder_process.py` 的 JS 注入会产生 `uncheck` 动作，而 `script_gen.py` 和前端 `step.ts` 未注册该动作，导致取消勾选步骤无法生成脚本和回放。

## 变更内容

1. `rec_ws.py`: 从调用 `start_codegen()`（Mode A）改为启动 `recorder_process.py` 子进程（Mode B）
2. `script_gen.py`: 新增 `uncheck` 动作处理器
3. `step.ts`: `ACTION_NAMES` 和 `STEP_SCHEMAS` 新增 `uncheck` 条目

## 功能 (Capabilities)

### 修改功能

- `case-recording`: 录制后端从 playwright codegen CLI 切换到注入 JS 的 Playwright sync API 方案
- `case-playback`: 脚本生成和回放新增 uncheck 动作支持

## 影响

- `backend/app/ws/rec_ws.py` — 核心改造，启动子进程方式变更
- `backend/app/services/script_gen.py` — 新增 uncheck handler
- `frontend/src/types/step.ts` — 新增 uncheck ActionName 和 Schema
