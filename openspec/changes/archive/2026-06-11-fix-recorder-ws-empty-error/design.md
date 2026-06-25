## 上下文

`backend/app/ws/rec_ws.py` 中 `_run_recorder` 调用 `start_codegen`（来自 `backend/app/services/recorder.py`）时，async generator 在 uvicorn 的 `asyncio.create_task` 上下文中抛出异常，且 `str(e)` 返回空字符串。WS 测试已验证：后端收到 `{cmd:"start"}` 后立即回复 `{"event":"error","message":""}`。

前端 `RecorderPanel.vue` 的 `start()` 函数未防止重复调用，可能导致多个 WebSocket 连接。

## 目标 / 非目标

**目标：**
- 暴露 `_run_recorder` 中真实异常信息（traceback）到前端和日志
- 防止 `RecorderPanel.vue` 重复点击导致的 WS 竞态
- 根据暴露的异常修复根因

**非目标：**
- 不涉及 Playwright 代码生成功能本身的增强
- 不涉及 UI 风格的改动

## 决策

1. **异常诊断方案** — 使用 `traceback.format_exc()` 而非仅 `str(e)`，因为 `str(e)` 可能为空；同时用 `logging.error()` 确保异常写入后端日志
2. **前端守卫** — `start()` 入口检查 `ws?.readyState === WebSocket.OPEN` 防止重复连接；`stop()` 检查 readyState 避免在已关闭的连接上发送数据
3. **根因修复策略** — 根据诊断暴露的异常类型决定最终修复方案

## 风险 / 权衡

- 诊断日志含 traceback 可能暴露内部路径 → 仅限于开发环境日志，不对外暴露
- 前端守卫不能完全消除时序问题 → 后端应有幂等性保障
