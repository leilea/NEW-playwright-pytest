## 为什么

用户在录制测试用例时，点击"开始录制"后打开的 Chromium 浏览器地址栏为空（about:blank），无法自动导航到输入的 URL，必须手动输入。同时，用例回放功能在 Windows 环境下持续报错 `NotImplementedError`，`asyncio.create_subprocess_exec` 调用完全不可用。两个 bug 分别导致录制和回放核心流程中断。

## 变更内容

1. **修复录制时 URL 丢失**: `recorder_process.py` 第 165 行在浏览器打开后冗余重读环境变量，覆盖了第 117 行已成功读取的 URL。若子进程环境变量在 PWDEBUG 模式下丢失，则 `page.goto("")` 停留在 about:blank。
2. **修复 Windows 子进程 NotImplementedError**: `main.py` 未设置 Windows 事件循环策略，导致 `playback.py` 和 `runner.py` 中的 `asyncio.create_subprocess_exec` 在非 ProactorEventLoop 下崩溃。

## 功能 (Capabilities)

### 新增功能
<!-- 无新增功能，仅修复已有功能的 bug -->

### 修改功能
- `case-recording`: 修复录制启动时目标 URL 未导航到浏览器的 bug
- `case-playback`: 修复 Windows 环境下回放 `asyncio.create_subprocess_exec` 报 NotImplementedError 的 bug

## 影响

- `backend/app/services/recorder_process.py` — 删除第 165 行冗余环境变量重读
- `backend/app/main.py` — 文件顶部添加 Windows ProactorEventLoop 策略设置
- `backend/app/services/playback.py` — 间接受益（事件循环策略修复后可用）
- `backend/app/services/runner.py` — 间接受益（同上）
