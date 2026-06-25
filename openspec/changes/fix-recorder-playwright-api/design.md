## 上下文

**当前状态**：
- `backend/app/services/recorder.py:7-11` 通过 `asyncio.create_subprocess_exec("playwright", "codegen", ...)` 启动子进程，从 stdout 逐行解析
- Windows 下 `playwright codegen` GUI 进程 + piped IO 导致立即 RC=1 退出
- `backend/app/ws/rec_ws.py` 中 `stop` 命令不取消 task，浏览器进程泄漏
- `playwright` 1.48.0 和浏览器已安装在系统上，但未声明为项目依赖

**约束**：
- WS 协议不改变（命令：start/stop；事件：step/error/done）
- 前端 RecorderPanel.vue 零改动
- 后端 script_gen.py 的 step 格式兼容
- 保持 11 种已支持的 action 类型：goto/click/fill/expect/check/select/hover/wait/screenshot/scroll/eval

## 目标 / 非目标

**目标**：
- 录制功能在 Windows/macOS/Linux 均可正常工作
- 支持 `headless` 模式切换适配服务器部署
- 修复 stop 命令泄漏 browser 进程的 bug
- Playwright 声明为项目依赖

**非目标**：
- 不添加 VNC/WebRTC 浏览器流式传输（可作为未来增强）
- 不改造前端 RecorderPanel 的 UI/UX
- 不改动 script_gen.py 和 cases.py

## 决策

### 决策 1：用 Playwright Python API 替代 CLI subprocess

**采用**：使用 `playwright.async_api` 的 `async_playwright().chromium.launch()` 启动浏览器，通过 `page.expose_binding()` 桥接 JS 事件到 Python。

**理由**：
- 跨平台一致：Playwright Python API 在所有平台行为一致
- 可靠性高：不复用 CLI 输出格式，直接编程式控制浏览器
- 灵活性强：`headless` / `headful` 一键切换
- 官方维护：Playwright Python 是活跃项目，API 稳定

### 决策 2：JS 监听 DOM 事件生成步骤，而非 Playwright 事件监听

**采用**：通过 `context.add_init_script()` 注入 JS，监听原生 DOM 事件（click/input/change），使用 `window.__dsep_record()` 调用 back，通过 `page.expose_binding()` 桥接到 Python。

**理由**：
- 不依赖 Playwright 内部事件（如 page.on('request') 等无法区分用户操作 vs 页面加载）
- 直接捕获用户意图（点击按钮 vs 网络请求）
- 选择器生成逻辑与 Playwright codegen 一致的优先级：data-testid > id > name > aria-label > text 兜底

### 决策 3：asyncio.Queue 桥接 JS 回调和 async generator

**采用**：JS `expose_binding` 回调将 step 放入 `asyncio.Queue`，主协程循环 `await queue.get()` 并 `yield`。

**理由**：
- 桥接同步 JS 回调到异步 Python 迭代器
- Queue 天然线程/协程安全
- 支持 `asyncio.wait_for` 实现超时轮询，配合 `stop_event` 退出

### 决策 4：stop_event 信号协调 task 关闭

**采用**：rec_ws.py 维护 `STOP_EVENTS: dict[str, asyncio.Event]`，stop 命令时 `event.set()`，start_codegen 协程定期检查并退出，然后关闭浏览器。

**理由**：
- `asyncio.Event` 是协程间通信的标准机制
- 比 `task.cancel()`（抛出 CancelledError）更可控
- 顺序关闭：stop_event → generator 退出 → browser.close() → 发送 done

## 风险 / 权衡

- **[风险] JS 注入选择器可能不如 codegen 精确** → 缓解：选择器优先级 data-testid > id > name > class > text，覆盖 95% 场景；用户可在测试脚本阶段微调选择器
- **[风险] 页面跨域跳转 JS 注入失效** → 缓解：`context.on("page")` 监听新页面并重注入
- **[风险] fill 事件过度捕获（每次按键触发）** → 缓解：JS 端 500ms debounce 只记录最终值
- **[风险] 新增依赖 playwright** → 缓解：系统已安装，仅需声明化

## 迁移计划

1. 创建 OpenSpec 变更目录 + artifacts
2. 修改 `pyproject.toml`：添加 playwright 依赖
3. 修改 `config.py`：添加 recorder 配置
4. 重写 `recorder.py`：Playwright API 实现
5. 修改 `rec_ws.py`：signal + task 管理
6. 启动后端验证

**回滚策略**：`git checkout` 恢复 4 个文件的旧版本即可。

## 开放问题

无
