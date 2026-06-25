## 修改需求

### 需求:录制过程
用户输入目标 URL 并点击"开始录制"后，系统必须启动 Playwright 浏览器并自动导航到指定 URL。

#### 场景:启动录制
- **当** 用户在 `/suites/:id` 页面点击"录制新用例"按钮
- **那么** 系统展开 RecorderPanel 组件，显示 URL 输入框和"开始录制"按钮

#### 场景:录制过程
- **当** 用户输入目标 URL 并点击"开始录制"
- **那么** 前端通过 WebSocket (`/ws/rec`) 发送 `{cmd: "start", url: "..."}` 到后端
- **那么** 后端启动 `recorder_process.py` 子进程，通过 `RECORDER_URL` 环境变量传递目标 URL
- **那么** 子进程使用 Playwright sync API 启动 Chromium 浏览器，导航到目标 URL，注入 JS 脚本捕获用户交互
- **那么** 浏览器启动后必须自动导航到用户输入的目标 URL
- **那么** 录制过程中，子进程通过 stdout JSON lines 输出步骤，后端实时转发 `{event: "step", step: {action, params}}` 到前端

#### 场景:URL 为空时录制
- **当** 用户未输入 URL 即点击"开始录制"
- **那么** recorder_process 子进程检测到空 URL 后立即终止并输出错误事件，后端转发到前端，禁止启动浏览器

#### 场景:保存录制结果
- **当** 用户点击"保存为新用例"并输入用例名称
- **那么** 系统通过 `POST /api/cases` 将 {suite_id, name, steps} 保存为新的测试用例
- **那么** 用例列表自动刷新，新用例出现在列表中

## 新增需求

### 需求:录制动作覆盖
录制系统必须捕获 checkbox 的 check 和 uncheck 两种状态变化。

#### 场景:勾选 checkbox
- **当** 用户在录制过程中勾选一个 checkbox
- **那么** 录制系统生成 `{action: "check", selector: "..."}` 步骤

#### 场景:取消勾选 checkbox
- **当** 用户在录制过程中取消勾选一个 checkbox
- **那么** 录制系统生成 `{action: "uncheck", selector: "..."}` 步骤
