## 上下文

当前录制链路 `RecorderPanel.vue → WS /ws/rec → rec_ws.py → recorder.py(start_codegen)` 使用 `playwright codegen --target=python` CLI 子进程。该方案有两个问题：Windows 上 asyncio 子进程启动不稳定；`codegen` 不会实时流式输出步骤（结束时才一次性输出）。`recorder_process.py`（Mode B）已实现：使用 `playwright.sync_api` 启动浏览器 + 注入 JS 捕获事件 + stdout JSON lines 实时输出，但未接入 WebSocket。

## 目标 / 非目标

**目标：**
1. `rec_ws.py` 的 `_run_recorder()` 从调用 `start_codegen()` 改为启动 `recorder_process.py` 子进程
2. `script_gen.py` 新增 `uncheck` handler，确保 uncheck 步骤能生成 `page.uncheck()` 代码
3. `step.ts` 新增 `uncheck` 到 `ACTION_NAMES` 和 `STEP_SCHEMAS`，确保 StepEditor 正常渲染

**非目标：**
- 不修改 `recorder_process.py` 本身（已完整）
- 不修改 `recorder.py`（Mode A 保留但不再使用）
- 不添加 `expect`/`wait`/`scroll`/`hover` 等录制时未捕获的动作的自动注入

## 决策

**决策：rec_ws.py 用 asyncio subprocess 启动 recorder_process.py**

理由：`recorder_process.py` 是独立子进程（`if __name__ == "__main__": main()`），通信协议是 stdin/stdout JSON lines。用 `asyncio.create_subprocess_exec` 启动：
- 传入 `RECORDER_URL` 环境变量携带目标 URL
- 读 stdout 逐行 JSON → 转发 WS
- stop 时向 stdin 写入 `{"cmd":"stop"}`

替代方案：改写 `recorder_process.py` 为 async generator（`async_recorder()`），直接在 rec_ws.py 中 import 调用。不选——子进程隔离更好，且 recorder_process 内部用 `threading.Event` 实现阻塞循环，改 async 风险高。

**决策：只处理 uncheck 动作，不在 script_gen 里添加 uncheck 的 action 到 ACTION_NAMES**

`recorder_process.py` 对 checkbox 使用独立 `check`/`uncheck` action。`_HANDLERS` 新增 `uncheck` → `page.uncheck(selector)` 即可。前端 `ACTION_NAMES` 加 `uncheck`，`STEP_SCHEMAS` 加对应 schema。

## 风险 / 权衡

[风险] 子进程在 Windows 上可能因路径问题找不到 Python 或 recorder_process.py → 使用 `sys.executable` 作为 Python 路径 + 项目内绝对路径定位文件
[风险] stdout/stderr 缓冲导致事件延迟 → `recorder_process.py` 已有 `sys.stdout.flush()`，对子进程设置 `PYTHONUNBUFFERED=1`
