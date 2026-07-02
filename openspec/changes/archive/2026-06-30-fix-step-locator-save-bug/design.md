## 上下文

`StepEditor.vue` 使用独立的 `editCache` Map 来存储用户输入的定位器值（显示格式为 `page.locator(...)` 等），与 `row.selector`（存储格式为 `__placeholder:xxx` 等）分开管理。`flushEditCache()` 在保存时将缓存写入 `row.selector`。

问题：`deep: true` 的 watch 在步骤数组任何深度属性变化时触发 `editCache.clear()`，造成用户正在输入的定位器数据丢失。

## 目标 / 非目标

**目标：**
1. `editCache` 不被步骤数组的无关属性变化清除
2. 保存后前端显示与后端存储同步

**非目标：**
- 不重构 `editCache` 整体架构（双源真值问题暂不改动）

## 决策

### D1: editCache 增量维护

watch 从"全量清空重建"改为"增量维护"：
- `editCache.get(s)` 存在的条目保留（用户正在编辑的值）
- 不存在的条目（新增步骤）自动初始化
- 已从数组中移除的步骤条目自动删除

### D2: save() 使用 API 返回值

`casesApi.update()` 返回更新后的 `Case` 对象，直接赋值给 `form.value.steps`，确保前端显示与服务端一致。

## 风险 / 权衡

- [风险] editCache 不清理旧值，如果用户修改 `row.selector` 但未重新编辑定位器，缓存可能保留旧逻辑值 → **缓解**: `onLocatorBlur` 已在 blur 时同步写入 `row.selector` + 更新缓存
