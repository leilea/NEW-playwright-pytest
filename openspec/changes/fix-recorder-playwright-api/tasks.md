## 1. 项目配置

- [x] 1.1 修改 `backend/pyproject.toml`：在 `dependencies` 中添加 `"playwright>=1.48"`
- [x] 1.2 修改 `backend/app/config.py`：添加 `recorder_headless: bool = False` 和 `recorder_browser: str = "chromium"`

## 2. 核心服务

- [x] 2.1 重写 `backend/app/services/recorder.py`：使用 Playwright Python API 实现 `start_codegen()`，核心逻辑包括：
  - `async with async_playwright() as p:` 启动 browser
  - `context.add_init_script(RECORDER_INJECT_JS)` 注入事件监听 JS
  - `page.expose_binding("__dsep_record", on_record)` 桥接 JS → Python
  - `asyncio.Queue` 缓冲回调数据
  - while 循环 `await queue.get(timeout=0.5)` + check `stop_event`
  - 支持 11 种 action：goto/click/fill/expect/check/select/hover/wait/screenshot/scroll/eval

## 3. WebSocket 管理器

- [x] 3.1 修改 `backend/app/ws/rec_ws.py`：
  - 新增 `STOP_EVENTS: dict[str, asyncio.Event]` 和 `REC_TASKS: dict[str, asyncio.Task]`
  - `start` 命令：创建 stop_event + task，存入字典
  - `stop` 命令：`event.set()` + `task.cancel()` + 发送 stopped
  - `WebSocketDisconnect` / `finally`：清理信号 + 取消 task
  - `_run_recorder` 传递 stop_event 到 `start_codegen()`

## 4. 验证

- [ ] 4.1 启动后端 `uvicorn app.main:app --reload`，确认无导入错误
- [ ] 4.2 打开前端录制页面，点击"开始录制"，确认浏览器窗口打开，无"录制错误"提示
- [ ] 4.3 在打开的浏览器中操作（点击、输入等），确认前端实时显示步骤
- [ ] 4.4 点击"停止"，确认浏览器关闭，前端显示 done
