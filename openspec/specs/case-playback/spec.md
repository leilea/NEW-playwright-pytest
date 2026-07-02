## 需求

### 需求:用例步骤回放
用户必须能从用例详情页点击"回放"按钮执行录制的用例步骤并查看结果。

#### 场景:触发回放
- **当** 用户在 `/cases/:id` 页面点击"回放"按钮
- **那么** 系统通过 WebSocket (`/ws/playback`) 发送 `{action: "start", case_name, steps, browser}` 到后端
- **那么** 系统进入回放等待状态，显示 loading 指示器

#### 场景:回放成功
- **当** 后端回放执行成功（exit code 0）
- **那么** 前端接收 `{type: "done", status: "passed", stdout, stderr, rc}` 
- **那么** 显示绿色"通过"状态，展开 stdout 输出内容

#### 场景:回放失败并显示错误日志
- **当** 后端回放执行失败（exit code ≠ 0）
- **那么** 前端接收 `{type: "done", status: "failed", stdout, stderr, rc}`
- **那么** 显示红色"失败"状态
- **那么** stdout 和 stderr 内容完整展示，关键错误信息高亮

#### 场景:回放超时或异常
- **当** WebSocket 连接断开或后端返回 `{type: "error"}`
- **那么** 前端显示"回放异常"提示和错误信息

### 需求:脚本预览
用户必须能在用例详情页查看生成的 pytest 脚本。

#### 场景:查看脚本
- **当** 用户进入 `/cases/:id` 页面
- **那么** 系统通过 `GET /api/cases/:id/script` 获取生成的 pytest 脚本
- **那么** 脚本内容在可折叠面板中以代码格式展示

#### 场景:复制脚本
- **当** 用户点击"复制脚本"按钮
- **那么** 生成的脚本内容复制到系统剪贴板

#### 场景:uncheck 步骤脚本生成
- **当** 用例包含 action 为 `uncheck` 的步骤
- **那么** 生成的 pytest 脚本中该步骤对应 `page.uncheck("selector")` 代码

### 需求:跨平台回放执行
回放功能必须在 Windows、macOS 和 Linux 平台上均正常工作。`asyncio.create_subprocess_exec` 调用必须使用正确的异步事件循环策略。

#### 场景:Windows 环境下启动回放
- **当** 用户在 Windows 平台的 `/cases/:id` 页面点击"回放"按钮
- **那么** 系统通过 WebSocket (`/ws/playback`) 发送回放请求
- **那么** 后端必须使用 `ProactorEventLoop` 事件循环策略执行 pytest 子进程
- **那么** 子进程正常启动并返回回放结果，禁止抛出 `NotImplementedError`

### 需求:回放脚本自动关闭对话框遮罩

生成的回放脚本必须在每个交互动作（click, fill, hover, check, select）之前检测并关闭可见的对话框遮罩。

#### 场景:comp_dialog_warp 遮罩拦截点击

- **当** 目标页面存在可见的 div.comp_dialog_warp 遮罩且其中包含可关闭按钮
- **那么** 脚本在点击目标元素前自动点击遮罩内的关闭按钮（.el-dialog__close, .el-icon-close, [aria-label='Close'] 等）
- **那么** 等待 300ms 确保关闭动画完成
- **那么** 然后执行目标点击动作

#### 场景:Element Plus 对话框拦截操作

- **当** 目标页面存在可见的 .el-dialog__wrapper 遮罩
- **那么** 脚本自动关闭该对话框后再执行原定交互动作

#### 场景:不存在遮罩时正常执行

- **当** 目标页面不存在任何可见的遮罩元素
- **那么** 脚本直接执行原定交互动作，无额外开销

### 需求:遮罩关闭失败时静默继续

#### 场景:自定义弹窗没有标准关闭按钮

- **当** 页面存在可见遮罩但没有匹配的关闭按钮选择器
- **那么** 脚本静默跳过关闭逻辑
- **那么** 继续执行原定交互动作

### 需求:遮罩选择器列表可配置

#### 场景:用户需要支持自定义遮罩类名

- **当** 目标应用使用 .my-app-dialog 作为遮罩类名
- **那么** 用户可在 OVERLAY_SELECTORS 常量中添加该选择器
- **那么** 后续生成的脚本会检测该遮罩

### 需求:遮罩拦截错误可识别

回放失败时系统必须能识别 overlay 拦截错误并输出友好提示。

#### 场景:拦截错误识别

- **当** Playwright 错误输出包含 "intercepts pointer events" 关键字
- **那么** `_parse_playback_error` 返回 `{type: "overlay_intercepted", detail: "元素被弹窗遮罩遮挡，请检查弹窗是否关闭"}`
