## 1. 创建自定义指令

- [x] 1.1 创建 `frontend/src/directives/tableResizable.ts`：实现 `v-table-resizable` 自定义指令
  - `mounted` 生命周期中查找 el-table 内部的 `<colgroup><col>` 和 `<thead><th>` 元素
  - 为每个 `<th>`（除最后一列操作列外）右侧添加 4px 绝对定位的拖拽手柄 `<div>`
  - 手柄 hover 时显示浅蓝色竖线，光标变为 `col-resize`
  - `mousedown` 记录起始 X 坐标和对应 `<col>` 的当前 width
  - `document.mousemove` 计算偏移量，更新 `<col width>` 属性，同时设置 `<th>` 和对应列 `<td>` 的 `style.width`
  - `document.mouseup` 移除事件监听，完成拖拽
  - 最小宽度约束：`minWidth` 默认 60px，通过指令参数 `v-table-resizable="{ minWidth: 60 }"` 可配置

## 2. 注册全局指令

- [x] 2.1 修改 `frontend/src/main.ts`：导入 `tableResizable` 指令并全局注册
  ```ts
  import vTableResizable from './directives/tableResizable'
  app.directive('table-resizable', vTableResizable)
  ```

## 3. 修改 Suites.vue

- [x] 3.1 修改 `frontend/src/pages/Suites.vue`：
  - 在 `<el-table>` 上添加 `v-table-resizable` 指令
  - 将各列 `min-width` 改为 `width`：系统名称(250)、版本号(120)、描述(300)、系统创建日期(180)
  - 保留序号(60)和操作(280)的 `width` 不变

## 4. 修改 SuiteDetail.vue

- [x] 4.1 修改 `frontend/src/pages/SuiteDetail.vue`：
  - 在 `<el-table>` 上添加 `v-table-resizable` 指令
  - 将各列 `min-width` 改为 `width`：名称(220)、标签(180)、创建时间(180)
  - 保留序号(60)、步骤数(80)和操作(160)的 `width` 不变

## 5. 验证

- [x] 5.1 启动前端 dev server，打开 `/suites` 页面，验证：各列有默认宽度，表头右边框 hover 时光标变为 col-resize，拖拽可调整列宽，操作列不可拖拽
- [x] 5.2 打开 `/suites/:id` 页面，验证：同上的列宽拖拽功能
- [x] 5.3 运行 `npm run build`（或 `npm run typecheck`）确认无编译错误
