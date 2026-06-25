## 上下文

当前项目前端路由结构：
- `/suites` → Suites.vue（套件列表）
- `/suites/:id` → SuiteDetail.vue（套件详情，仅显示简单用例列表）
- `/cases` → Cases.vue（独立用例页，含套件过滤）
- `/cases/:id` → CaseEditor.vue（用例编辑器，Record/Playback 按钮为 TODO 占位）

后端录制和回放 WebSocket 已完备但前端未对接。

## 目标 / 非目标

**目标：**
- 用例管理作为套件的子页面，路由从 `/cases` 迁移到 `/suites/:id` 内部的用例列表
- "新增用例"按钮触发 Playwright codegen 录制（WebSocket → recorder.py → 实时步骤）
- 用例详情页集成脚本预览（script_gen.py）和回放（playback.py）功能，含报错日志展示
- 修复 RecorderPanel.vue 前后端 WebSocket 协议不匹配

**非目标：**
- 不修改后端 API（后端已完备）
- 不修改数据库模型
- 不改变 Suite → Case 的外键关系

## 决策

### 1. 路由结构：移除 `/cases`，强化 `/suites/:id`
- **选择**：把 Cases.vue 的功能合并到 SuiteDetail.vue，`/suites/:id` 成为用例管理中心
- **替代方案**：保留 `/cases` 但加套件 filter — 用户操作路径更长，不符合"二级页面"语义
- **理由**：用例天然属于套件，从套件进入最直接；减少一层路由

### 2. 录制流程：RecorderPanel 嵌入 SuiteDetail，通过 WebSocket 实时接收
- **选择**：RecorderPanel 作为 SuiteDetail 的子组件，录制完成后 emit `create-case` 事件
- **替代方案**：弹出独立录制页面 — 增加路由复杂度，不符合"从测试用例页面新增"的直觉
- **理由**：同页面操作减少上下文切换，录制步骤实时可见

### 3. 回放流程：CaseEditor 内 WebSocket 直连 playback_ws
- **选择**：CaseEditor 内建 playback panel，发送 `{action:"start", case_name, steps, browser}` → 接收结果
- **理由**：步骤编辑和回放验证在同一页面，反馈循环最短

### 4. WebSocket 协议修复：前端适配后端
- **选择**：修改前端 RecorderPanel 的 send/recv 字段名以匹配后端
- **理由**：后端 `rec_ws.py` 发送 `{event: "step", step: {action, params}}`，前端误读 `type: "log"`；后端读 `cmd`，前端发 `action`

## 风险 / 权衡

- **录制保存时机**：录制停止后需用户输入用例名再保存 — 需处理用户在录制中途关闭页面的情况（数据丢失）
- **回放大脚本**：playback_ws 的 `run_playback()` 是同步阻塞子进程，大脚本可能超时 → 前端设置合理的 WebSocket 超时 + 显示 loading 状态
- **Cases.vue 移除**：如其他地方（Dashboard 等）引用了 `/cases` 路由，需更新链接
