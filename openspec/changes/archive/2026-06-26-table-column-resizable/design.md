## 上下文

项目使用 Vue 3 + Element Plus 2.7 作为前端框架。`el-table` 组件本身不提供列宽拖拽调整功能（v2.x 中无 `resizable` 属性）。当前系统用例列表（`Suites.vue`）和系统用例内的测试用例列表（`SuiteDetail.vue`）的列宽使用 `min-width` 弹性分配，缺少固定初始宽度，用户无法手动调整列宽。

已探索过的替代方案及拒绝原因：
- **colResizable（jQuery 插件）**：需要引入 jQuery，与 Vue 3 架构冲突，DOM 操作可能被 Vue 覆写
- **替换为 vxe-table**：改动量大，需重写两个页面的表格代码，且 vxe-table 的部分行为（表单渲染、自定义模板）与 el-table 不同
- **`element-plus-column-resize` 等第三方 npm 包**：质量参差，维护频率低，引入不可靠依赖

## 目标 / 非目标

**目标：**
- 为 Suites.vue 和 SuiteDetail.vue 的 el-table 添加列宽拖拽调整功能
- 设置合理的默认列宽（固定 `width` 替代 `min-width`）
- 鼠标拖拽表头右边框实时调整列宽
- 操作列不可拖动（固定宽度）

**非目标：**
- 不替换 el-table 为 vxe-table 或其他表格库
- 不引入 jQuery 或任何外部依赖
- 不处理其他页面（Runs.vue / Reports.vue / StepEditor.vue）的列宽
- 不持久化列宽（不保存到 localStorage）

## 决策

1. **自定义 Vue 3 指令**：使用 `v-table-resizable` 自定义指令，挂载到 `<el-table>` 元素上。指令在 `mounted` 生命周期中查找表格内部的 `<colgroup><col>` 元素和 `<thead><th>` 元素，为每个 `<th>` 添加拖拽手柄。

2. **通过 `<col width>` 更新列宽**：el-table 内部使用 `<table>` + `<colgroup>` 布局。拖拽时更新对应 `<col>` 的 `width` 属性，el-table 会基于此自动响应。同时设置对应列的 `<th>` 和 `<td>` 的 `style.width` 作为备选。

3. **拖拽手柄**：每个 `<th>`（除操作列外）右侧放置一个 4px 宽的绝对定位手柄，默认透明，hover 时显示浅蓝色指示线。采用 `col-resize` 光标。

4. **事件处理**：`mousedown` 开始拖拽（记录初始 X 坐标和列宽），`mousemove` 计算偏移量更新列宽，`mouseup` 停止拖拽。事件绑定到 `document` 以避免拖出表头时丢失跟踪。

5. **最小宽度**：默认 60px，防止列宽缩到不可见。

6. **禁用列**：默认最后一列（操作列）不可拖动，因为其宽度固定且不需要调整。

## 风险 / 权衡

- **[风险] Vue 响应式渲染可能重置指令修改的列宽** → 使用 MutationObserver 监听表格 DOM 变化，在 el-table 重新渲染后重新应用列宽
- **[风险] 拖拽时性能问题** → 拖拽手柄不触发列内容重绘，仅在 `mouseup` 时一次性应用最终宽度（如果未来启用 liveDrag 则实时更新）
- **[权衡] 不持久化列宽** → 简化实现；页面刷新后列宽恢复默认值，保持一致的初始体验
