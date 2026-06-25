## 新增需求

### 需求:跨平台回放执行
回放功能必须在 Windows、macOS 和 Linux 平台上均正常工作。`asyncio.create_subprocess_exec` 调用必须使用正确的异步事件循环策略。

#### 场景:Windows 环境下启动回放
- **当** 用户在 Windows 平台的 `/cases/:id` 页面点击"回放"按钮
- **那么** 系统通过 WebSocket (`/ws/playback`) 发送回放请求
- **那么** 后端必须使用 `ProactorEventLoop` 事件循环策略执行 pytest 子进程
- **那么** 子进程正常启动并返回回放结果，禁止抛出 `NotImplementedError`
