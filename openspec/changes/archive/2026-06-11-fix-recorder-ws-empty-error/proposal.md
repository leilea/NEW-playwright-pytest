## 为什么

点击"开始录制"按钮后，Playwright 浏览器未启动，前端闪现"录制中"后立即显示"录制错误"。根因是 `start_codegen` 在 uvicorn 的 `asyncio.create_task` 上下文内抛出了一个消息为空的异常，导致前端收到 `{"event":"error","message":""}` 而无法定位问题。

## 变更内容

1. **后端诊断增强** — `_run_recorder` 异常捕获中加入 `traceback.format_exc()` 和 `logging.error`，确保真实异常信息可见
2. **前端竞态修复** — `RecorderPanel.vue` 的 `start()` 加入防重复点击守卫，`stop()` 加入 readyState 检查
3. **根因修复** — 根据暴露的真实异常针对性修复（预判：Windows 下异步事件循环策略兼容问题）

## 功能 (Capabilities)

### 新增功能
- `recorder-error-visibility`: 录制功能的错误信息完整可见，包含完整 Python traceback

### 修改功能
<!-- 无现有规范变更 -->

## 影响

- `backend/app/ws/rec_ws.py` — `_run_recorder` 异常处理增强
- `frontend/src/components/RecorderPanel.vue` — 竞态守卫 + readyState 检查
