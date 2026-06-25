## 上下文

当前录制和回放流程在 Windows 环境下存在两个阻断性 bug：

1. **录制**: 前端通过 WebSocket 将 URL 传递到后端 → `recorder.py` 设置 `RECORDER_URL` 环境变量 → `recorder_process.py` 子进程读取并导航。子进程在第 117 行首次读取 URL 用于 `started` 事件，但在第 165 行再次读取环境变量进行实际导航。若浏览器启动过程中环境变量被清除（PWDEBUG 模式可能触发此行为），第二次读取返回空字符串，`page.goto("")` 导致浏览器停留在 `about:blank`。

2. **回放**: `playback.py` 和 `runner.py` 使用 `asyncio.create_subprocess_exec` 启动 pytest 子进程。Windows 下子进程支持需要 `ProactorEventLoop`，但主 FastAPI 进程未显式设置事件循环策略，uvicorn 运行时可能回退到不支持子进程的 `SelectorEventLoop`。

## 目标 / 非目标

**目标：**
- 录制时浏览器正确导航到用户输入的 URL
- Windows 环境下回放 `asyncio.create_subprocess_exec` 正常工作

**非目标：**
- 不修改录制/回放的业务逻辑或协议
- 不添加新功能
- 不重构代码架构

## 决策

### 决策 1: 删除 redundant URL 重读而非增加保护逻辑

**方案**: 删除 `recorder_process.py` 第 165 行的冗余 `target_url = os.environ.get("RECORDER_URL", "")`

**理由**: 第 117 行已在一个线程安全的时间点（浏览器启动前）读取了 URL，后续整个 `main()` 函数中 `target_url` 变量保持在闭包作用域内。第 165 行的重读无实际用途，反而引入了环境变量被覆盖的风险。

**替代方案**: 
- 增加 `if not target_url: raise` 验证 → 只是报告错误，不修复根因
- 保存到文件再读取 → 过度设计

### 决策 2: 在 main.py 顶部设置事件循环策略

**方案**: 在 `backend/app/main.py` 第 1 行之前插入 Windows ProactorEventLoop 策略设置

**理由**: 与 `recorder_process.py:21-23` 完全一致的策略设置模式。必须在所有 import 之前执行，确保事件循环创建时策略已就绪。此修复同时覆盖 `playback.py` 和 `runner.py` 两处子进程调用。

**替代方案**:
- 在各子进程调用前局部设置 → 冗余、易遗漏
- 使用 `subprocess.Popen` 替代 `asyncio.create_subprocess_exec` → 需要重构异步流处理逻辑，风险更高
- 使用 `concurrent.futures.ProcessPoolExecutor` → 改变进程管理模型，影响 stdout/stderr 实时流式处理

## 风险 / 权衡

- [风险] 设置全局事件循环策略可能影响其他依赖 asyncio 的库 → 缓解：ProactorEventLoop 是 Python 3.8+ Windows 默认策略，此修复仅是显式声明，不改变默认行为。`recorder_process.py` 已在子进程中使用相同策略，无已知问题。
- [风险] 删除 URL 重读后，若未来有需求在浏览器启动后动态修改 URL → 缓解：当前架构不支持此场景，且可通过 stdin 命令实现动态 URL 切换，无需依赖环境变量重读。
