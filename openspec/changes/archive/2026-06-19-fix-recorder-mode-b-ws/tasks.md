## 1. 核心修复 — rec_ws.py 切换到 Mode B

- [x] 1.1 重写 `_run_recorder()` 使用 `asyncio.create_subprocess_exec` 启动 `recorder_process.py`，传入 `RECORDER_URL` 环境变量和 `PYTHONUNBUFFERED=1`
- [x] 1.2 实现 stdout JSON lines 读取循环，解析 `event` 字段并转发到 WebSocket（step/done/error）
- [x] 1.3 实现 stop 命令：向子进程 stdin 写入 `{"cmd":"stop"}`

## 2. 补充 — uncheck 动作支持

- [x] 2.1 `script_gen.py` `_HANDLERS` 新增 `uncheck` handler（调用 `page.uncheck()`）
- [x] 2.2 `frontend/src/types/step.ts` `ACTION_NAMES` 新增 `uncheck`
- [x] 2.3 `frontend/src/types/step.ts` `STEP_SCHEMAS` 新增 `uncheck` 条目

## 3. 验证

- [x] 3.1 验证 `script_gen.py` uncheck handler 生成正确代码
- [x] 3.2 验证 `rec_ws.py` 语法正确，子进程启动路径可用
