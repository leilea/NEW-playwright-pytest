## 为什么

在测试用例详情的"操作步骤"页面中，编辑 locator 参数时（如 `locator(".icon-SystemNavigation")`），将光标放到文本末尾按 Backspace 删除字符，内容会逐级嵌套损坏，例如按 2 次 Backspace 后变成 `locator("locator(\"locator(\\\".icon-SystemNavigation\\\"\"")`。这是由于分解式 v-model 在每次按键时触发「内部格式 → 显示格式 → 内部格式」的转换循环，当输入不完整时转换函数无法正确解析，返回的原始字符串又被二次包装，形成级联损坏。

## 变更内容

1. **StepEditor.vue**: selector 输入框从「`:modelValue` + `@update:modelValue`」分解式绑定改为本地编辑缓存（`reactive Map<Step, string>`）+ `@blur` 转换
2. **StepEditor.vue**: 暴露 `flushEditCache()` 方法，确保父组件 Save 前未 blur 的值也能被同步
3. **CaseEditor.vue**: Save 前调用 `flushEditCache()` 刷新未提交的编辑值

## 功能 (Capabilities)

### 新增功能
- 无新增功能

### 修改功能
- `case-recording`: 步骤编辑器中 selector/locator 参数的编辑行为以改善输入完整性和光标稳定性

## 影响

- `frontend/src/components/StepEditor.vue` — selector 输入绑定方式变更
- `frontend/src/pages/CaseEditor.vue` — Save 前增加 flush 调用
- 不影响后端、不影响其他参数字段（value、url、text、number、select）
