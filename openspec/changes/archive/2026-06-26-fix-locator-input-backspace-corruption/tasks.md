## 1. StepEditor.vue — 本地编辑缓存

- [x] 1.1 添加 `editCache`（`reactive(new Map<Step, string>())`），在 `watch(() => props.modelValue, ...)` 中按 steps 初始化缓存值
- [x] 1.2 将 selector 的 `<vxe-input>` 从 `:modelValue` / `@update:modelValue` 改为 `:modelValue` (`.get()`) + `@update:modelValue` (`.set()`) + `@blur`
- [x] 1.3 新增 `onLocatorBlur(row)` 函数：从 editCache 读取值 → 补 `page.` 前缀 → 调用 `locatorToSelector` → 写入 `row.selector`
- [x] 1.4 新增 `flushEditCache()` 函数：遍历 editCache 中所有条目执行 onLocatorBlur，然后 clear 缓存
- [x] 1.5 通过 `defineExpose({ flushEditCache })` 暴露 flush 方法

## 2. CaseEditor.vue — Save 前 flush

- [x] 2.1 为 `<StepEditor>` 添加 template ref
- [x] 2.2 在 `save()` 函数中，API 调用前调用 `stepEditorRef.value?.flushEditCache()`

## 3. 验证

- [ ] 3.1 前端 build 验证无编译错误（`npm run build --prefix frontend`）
- [ ] 3.2 手动验证：编辑 locator 末尾按 Backspace 无级联损坏、光标不跳转
- [ ] 3.3 手动验证：编辑后不 blur 直接 Save，selector 正确保存
