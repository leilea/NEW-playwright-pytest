## 1. 增强 `_findLabel()` — Element Plus 标签检测

- [x] 1.1 在 `_findLabel()` 中现有三种方式后，添加 `.el-form-item` 标签查找逻辑（`el.closest('.el-form-item')` → `.el-form-item__label`）
- [x] 1.2 验证: 确认新逻辑不影响标准 HTML label 检测（现有三种方式命中时不会执行到新代码）

## 2. 修复 `__role:role` 伪唯一性 bug

- [x] 2.1 将 `__role:role` 候选的 `unique: true` 改为 `unique: _countRoleMatches(role, '') <= 1`
- [x] 2.2 验证: 确认 `_countRoleMatches(role, '')` 在空名时正确计数（利用已有的 `count < 2` 上限，不会造成性能问题）

## 3. 增强 Phase 3 父级上下文回退

- [x] 3.1 在 Phase 3 中 `_findParentContext(el)` 返回 null 后，检查元素自身是否有合法 id（`! /^\d/.test(el.id)`），有则返回 `'#' + CSS.escape(el.id) + ' > ' + best.sel`
- [x] 3.2 验证: 确认链式选择器格式正确，`#id > __placeholder:xxx` 可被 `_locator()` 正确解析

## 4. 验证

- [x] 4.1 后端单元测试: 运行 `pytest backend/tests/ -v` 确认无回归
- [x] 4.2 前端类型检查: 运行 `vue-tsc --noEmit` 确认无错误
