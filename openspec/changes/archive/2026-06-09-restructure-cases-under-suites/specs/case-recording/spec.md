## 新增需求

### 需求:套件下录制新用例
用户必须能从套件详情页点击"录制新用例"按钮启动 Playwright codegen 录制功能。

#### 场景:启动录制
- **当** 用户在 `/suites/:id` 页面点击"录制新用例"按钮
- **那么** 系统展开 RecorderPanel 组件，显示 URL 输入框和"开始录制"按钮

#### 场景:录制过程
- **当** 用户输入目标 URL 并点击"开始录制"
- **那么** 前端通过 WebSocket (`/ws/rec`) 发送 `{cmd: "start", url: "..."}` 到后端
- **那么** 后端启动 playwright codegen 进程
- **那么** 录制过程中，前端实时接收 `{event: "step", step: {action, params}}` 并展示步骤列表

#### 场景:保存录制结果
- **当** 用户点击"保存为新用例"并输入用例名称
- **那么** 系统通过 `POST /api/cases` 将 {suite_id, name, steps} 保存为新的测试用例
- **那么** 用例列表自动刷新，新用例出现在列表中

### 需求:录制协议修复
RecorderPanel 前后端 WebSocket 协议必须一致。

#### 场景:发送命令
- **当** RecorderPanel 发送录制命令
- **那么** 必须使用 `cmd` 字段（而非 `action`），值为 `"start"` 或 `"stop"`

#### 场景:接收步骤
- **当** RecorderPanel 收到 WebSocket 消息
- **那么** 必须通过 `msg.event` 字段判断消息类型（值为 `"step"`, `"done"`, `"error"`）
- **那么** step 消息的步骤数据直接从 `msg.step` 字段获取，无需二次解析
