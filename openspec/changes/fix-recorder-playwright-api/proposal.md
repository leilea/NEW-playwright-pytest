## 为什么

录制功能（Recorder）当前使用 `playwright codegen` CLI 子进程 + stdout 正则解析的实现方式，在 Windows 平台上根本不可用：`playwright codegen` 是 GUI 工具，通过 `asyncio.create_subprocess_exec()` 以 piped stdout 启动时立即 RC=1 退出。后端记录到 WS 的 error 事件，前端显示"录制错误"。

此外，CLI 方案存在 3 个架构问题：
1. **不可跨平台部署**：依赖 `playwright codegen` CLI 输出格式，Linux 服务器需要 X11，Windows 无法运行
2. **无法服务器部署**：`headless=False` 时需要物理显示器；`headless=True` 模式下 `codegen` CLI 不会产生可用输出
3. **子进程泄漏**：`rec_ws.py` 的 stop 命令仅 `break` 消息循环，从未取消 `_run_recorder` task，浏览器进程泄漏

## 变更内容

- **重写** `backend/app/services/recorder.py`：将 `playwright codegen` CLI 方案替换为 Playwright Python API 方案
- **修改** `backend/app/ws/rec_ws.py`：添加 `stop_event` 信号机制和 task 管理，修复子进程泄漏 bug
- **修改** `backend/app/config.py`：添加 `recorder_headless`、`recorder_browser` 配置项
- **修改** `backend/pyproject.toml`：添加 `playwright>=1.48` 依赖（系统已安装，仅声明化）

## 功能

### 新增功能
- `playwright-api-recorder`: 使用 Playwright Python API 的录制引擎，通过 JavaScript 注入监听 DOM 事件（click/input/change/select），`page.expose_binding()` 桥接回 Python 生成结构化 step 事件

### 修改功能
- `recorder-ws-manager`: rec_ws.py 新增 `STOP_EVENTS` 信号字典 + `REC_TASKS` 任务字典，支持优雅停止和浏览器清理

### 移除功能
- `parse_codegen_line` 正则解析函数：废弃，由 JS 直接生成结构化数据

## 影响

- **代码**：重写 recorder.py（~80 行）、修改 rec_ws.py（+15 行）、修改 config.py（+2 行）、修改 pyproject.toml（+1 行）
- **运行时**：新增 Playwright Python 依赖，浏览器生命周期由 Python API 管理
- **前端**：零改动，WS 协议完全兼容
- **用户可见行为**：录制按钮正常工作，浏览器窗口在服务器端打开，步骤实时推送到前端
- **可回滚**：恢复 4 个文件的旧版本即可
