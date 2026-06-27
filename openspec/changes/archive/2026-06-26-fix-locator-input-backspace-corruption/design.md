## 上下文

`StepEditor.vue` 中 selector 参数使用「`:modelValue` + `@update:modelValue`」分解式 v-model：每次按键都触发 `locatorToSelector` → 更新 `row.selector` → 重新渲染 → `selectorToLocator` 重新计算显示值。当用户在编辑中间按键（如 Backspace 删除末尾字符）时：

1. `locatorToSelector` 的正则 `/^page\.(.+?)\((.+)\)$/` 因输入不完整而匹配失败
2. 函数返回原始字符串（含 `page.` 前缀）作为 `row.selector`
3. 下次渲染时 `selectorToLocator` 又将这串内容二次包装进 `page.locator(...)`，形成级联嵌套损坏

同时，`:modelValue` 表达式每次返回新字符串引用，导致 vxe-input 光标跳至末尾。

## 目标 / 非目标

**目标：**
- 编辑 locator 时，光标不跳转，内容不级联损坏
- Save 前未 blur 的编辑值也能正确同步到内部 selector 格式

**非目标：**
- 不改变其他参数字段（value, url, text, number, select）的绑定方式
- 不改变 `locator.ts` 中 `selectorToLocator` / `locatorToSelector` 的逻辑
- 不影响后端

## 决策

### 决策 1：本地编辑缓存（而非 debounce 或修复正则）

**选择**：使用 `reactive(new Map<Step, string>())` 为每行维护独立的编辑字符串，vxe-input 通过 `v-model="editCache[row]"` 双向绑定到该缓存，仅在 `@blur` 时触发 `locatorToSelector` 转换。

**替代方案**：
- **修复 `locatorToSelector` 正则**：增加不回退逻辑处理不完整输入。但光标跳跃问题依然存在（`:modelValue` 每次返回新引用）。
- **debounce 转换**：在输入停止后才转换。同样无法解决光标跳跃问题，且在快速编辑时仍可能丢失中间状态。

**理由**：编辑缓存方案将"显示格式"和"内部格式"彻底解耦，光标不跳转（Vue 不会替换 v-model 绑定的值），只在明确提交（blur/save）时才转换。

### 决策 2：使用 `reactive(Map)` 而非普通 `ref` 对象

**选择**：`reactive(new Map<Step, string>())`。

**替代方案**：
- **`ref(new Map(...))`**：需要 `.value` 访问，模板中不便用。
- **行索引为 key 的普通对象**：步骤重排时索引会变，需要额外维护。

**理由**：Vue 3 支持 `reactive(Map)`，`v-model="editCache[row]"` 等价于 `get/set`，且 Step 对象引用稳定。

### 决策 3：暴露 `flushEditCache` 并通过 `defineExpose` 导出

**选择**：在 `StepEditor.vue` 中通过 `defineExpose({ flushEditCache })` 暴露 flush 方法，`CaseEditor.vue` 的 Save 函数中通过 template ref 调用。

**理由**：确保「编辑后直接点 Save 未 blur」的极端情况也能正确同步。

## 风险 / 权衡

- **vxe-input 的 v-model 对 Map 兼容性**：vxe-pc-ui 的 vxe-input 基于原生 input，v-model 行为与 Vue 3 标准一致，经测试 Map 绑定正常工作
- **editCache 内存泄漏**：Map 按 Step 对象引用索引，步骤删除后旧引用不再被访问，JS GC 会回收。无泄漏风险。
- **步骤新增/从外部刷新**：通过 `watch(() => props.modelValue, ...)` 在 steps 变化时全量重建 editCache，保证同步
