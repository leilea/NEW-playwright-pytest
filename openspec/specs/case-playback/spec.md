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

### 需求:回放支持自愈

系统执行回放时，必须支持可选的 pytest-breadcrumb 自愈机制。

#### 场景:启用 breadcrumb 回放
- **当** breadcrumb_enabled 配置为 true
- **那么** 生成的脚本使用 `crumb()` 包装 page 对象
- **那么** 首次回放时各元素指纹存入 `.breadcrumb.db`

#### 场景:关闭 breadcrumb
- **当** breadcrumb_enabled 配置为 false 或环境变量 `BREADCRUMB_ENABLED=false`
- **那么** 生成的脚本不包含 breadcrumb 包装，使用原始 Playwright page 对象

#### 场景:breadcrumb 自愈
- **当** 页面改版导致原始选择器失效
- **那么** pytest-breadcrumb 扫描全页匹配指纹
- **那么** 匹配成功后回放继续、不中断

### 需求:跨平台回放执行
回放功能必须在 Windows、macOS 和 Linux 平台上均正常工作。`asyncio.create_subprocess_exec` 调用必须使用正确的异步事件循环策略。

#### 场景:Windows 环境下启动回放
- **当** 用户在 Windows 平台的 `/cases/:id` 页面点击"回放"按钮
- **那么** 系统通过 WebSocket (`/ws/playback`) 发送回放请求
- **那么** 后端必须使用 `ProactorEventLoop` 事件循环策略执行 pytest 子进程
- **那么** 子进程正常启动并返回回放结果，禁止抛出 `NotImplementedError`
