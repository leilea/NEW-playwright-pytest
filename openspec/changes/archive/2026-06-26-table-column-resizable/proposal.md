## 为什么

系统用例列表（`/suites`）和系统用例内的测试用例列表（`/suites/:id`）使用 Element Plus `el-table`，列宽使用 `min-width` 弹性分配，缺少明确的初始宽度。当列内容过多（如长描述、多标签）时，文字被截断或换行，用户无法方便地查看完整内容，也无法手动拖拽表头边框调整列宽。

## 变更内容

- **新增** `frontend/src/directives/tableResizable.ts`：Vue 3 自定义指令 `v-table-resizable`，为 el-table 表头列添加拖拽手柄，支持鼠标拖拽调整列宽
- **修改** `frontend/src/main.ts`：全局注册 `v-table-resizable` 指令
- **修改** `frontend/src/pages/Suites.vue`：将 `min-width` 改为固定 `width`，添加 `v-table-resizable` 指令
- **修改** `frontend/src/pages/SuiteDetail.vue`：将 `min-width` 改为固定 `width`，添加 `v-table-resizable` 指令

## 功能 (Capabilities)

### 新增功能
- `table-column-resizable`: el-table 表头列宽拖拽调整功能 —— 支持鼠标拖拽表头右边框实时调整列宽，设置最小宽度约束，操作列不可拖动

### 修改功能
- 无（仅为现有表格增强交互，不改动业务逻辑）

## 影响

- **代码**：新增 1 个文件 + 修改 3 个文件（约 100 行新增、20 行修改）
- **运行时**：纯前端 Vue 指令实现，零额外依赖
- **测试代码**：无影响（项目无前端 UI 自动化测试）
- **用户可见行为**：表格列有固定初始宽度；鼠标悬停表头右边框时显示 `col-resize` 光标；拖拽可加宽或收窄列宽；操作列不可拖拽
- **可回滚**：移除指令 1 行 + 恢复 `min-width` 即可恢复；零破坏性变更
