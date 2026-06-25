## 1. 修复 RecorderPanel WebSocket 协议

- [x] 1.1 修改发送消息：`{action: 'start'}` → `{cmd: 'start'}`，`{action: 'stop'}` → `{cmd: 'stop'}`
- [x] 1.2 修改接收消息：`msg.type === 'log'` → `msg.event === 'step'`，`msg.type === 'done'` → `msg.event === 'done'`，`msg.type === 'error'` → `msg.event === 'error'`
- [x] 1.3 修改步骤解析：用 `msg.step`（后端已解析）替代 `parseLine(msg.text)`
- [x] 1.4 新增 emit: `@create-case` 事件，录制停止后触发，传出步骤数组和 URL

## 2. 重写 SuiteDetail.vue 为套件下用例管理页

- [x] 2.1 页头显示套件名称和描述（从路由 params.id 加载 suite 信息）
- [x] 2.2 集成 RecorderPanel 组件，点击"录制新用例"按钮展开录制面板
- [x] 2.3 监听 RecorderPanel 的 `@create-case` 事件，调用 `POST /api/cases` 创建新用例
- [x] 2.4 用例列表表格展示：名称、标签、步骤数、创建时间
- [x] 2.5 用例列表操作：点击名称→`/cases/:id`，删除按钮调用 `DELETE /api/cases/:id`
- [x] 2.6 "手动新建"按钮跳转 `/cases/new?suite_id=X`
- [x] 2.7 录制后用例名称输入弹窗

## 3. 重写 CaseEditor.vue 为详情+脚本预览+回放页

- [x] 3.1 加载用例数据：`GET /api/cases/:id`（含 steps），加载套件列表
- [x] 3.2 集成 StepEditor 组件用于步骤编辑
- [x] 3.3 脚本预览面板：`GET /api/cases/:id/script` 获取生成脚本，折叠展示
- [x] 3.4 回放按钮：通过 WebSocket (`/ws/playback`) 发送 `{action:"start", case_name, steps, browser}`
- [x] 3.5 回放结果面板：展示 status / stdout / stderr / rc，失败时 stderr 标红高亮
- [x] 3.6 保存按钮：`PUT /api/cases/:id` 更新步骤
- [x] 3.7 复制脚本按钮：将生成脚本复制到剪贴板

## 4. 更新路由和侧边栏

- [x] 4.1 router/index.ts：移除 `/cases` 独立路由，新增 `/cases/new` 路由
- [x] 4.2 MainLayout.vue：移除侧边栏"测试用例"菜单项
- [x] 4.3 SuiteDetail.vue 中"详情"路由保持不变（`/suites/:id`）
