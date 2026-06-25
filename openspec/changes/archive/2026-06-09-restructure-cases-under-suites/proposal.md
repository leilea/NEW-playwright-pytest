## 为什么

测试用例目前作为独立页面存在（`/cases`），与测试套件（`/suites`）之间缺乏层级关系。用户无法在套件上下文中直接创建和管理用例，录制和回放功能均未与 UI 打通。

## 变更内容

1. 将测试用例调整为测试套件的二级页面，移除独立的 `/cases` 路由入口
2. 套件详情页（`/suites/:id`）成为用例管理中心：显示用例列表 + 录制入口
3. 新增用例按钮启动 Playwright codegen 录制功能（WebSocket → `recorder.py`）
4. 用例详情页（`/cases/:id`）增加脚本预览（`script_gen.py`）和回放功能（`playback.py`），回放结果含报错日志
5. 修复 `RecorderPanel.vue` 前后端 WebSocket 协议不匹配问题

## 功能 (Capabilities)

### 新增功能
- `case-recording`: 从套件页面的"录制新用例"按钮启动 Playwright codegen 录制，通过 WebSocket 实时接收步骤，保存为新 Case
- `case-playback`: 用例详情页支持回放录制的步骤脚本，通过 WebSocket 发送步骤数据，接收执行结果和错误日志
- `suite-case-management`: 套件详情页成为完整的用例管理界面，包含录制入口、用例列表、创建/删除操作

### 修改功能
- `suite-detail`: 套件详情页从简单列表扩展为完整的用例管理中心
- `case-editor`: 用例编辑器增加脚本预览和回放功能面板

## 影响

- 前端路由 `/cases` 移除，用例入口统一从 `/suites/:id` 进入
- 侧边栏移除"测试用例"独立菜单项
- `RecorderPanel.vue` WebSocket 协议修正（`action` → `cmd`, `type` → `event`）
- `SuiteDetail.vue` 重写为用例管理页
- `CaseEditor.vue` 重写为编辑+脚本预览+回放页
- 后端代码无需修改
