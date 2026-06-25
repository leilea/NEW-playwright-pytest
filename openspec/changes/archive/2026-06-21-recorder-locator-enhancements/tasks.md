## 1. genSelector 重写 (recorder_process.py)

- [x] 1.1 实现 `_findLabel(el)` 辅助函数（aria-labelledby/labels属性/父级label）
- [x] 1.2 实现 `_inferRole(el)` 辅助函数（role属性+标签名推断）
- [x] 1.3 实现 `_scope(prefix, selector, el)` 统一追加 `|tag` 后缀
- [x] 1.4 重写 `genSelector()` 优先级链：label → aria-label → role+name → text(unique)/text(non-unique) → placeholder → role-only → data-testid → CSS id → name → tag
- [x] 1.5 `__text:` 前做唯一性检查：`document.evaluate` 计数，>1 个用 `|tag` 限定

## 2. _locator 转换 (script_gen.py)

- [x] 2.1 实现 `_raw_locator(sel)` 返回基础 Playwright API 调用
- [x] 2.2 实现 `_locator(sel)` 解析 `|tag` 后缀，生成 `locator(tag).filter(has=...)`
- [x] 2.3 删除旧的 `__text:tag:text` 特殊格式
- [x] 2.4 所有 handler 改用 `_locator(sel).action()` 链式调用

## 3. 智能等待

- [x] 3.1 `_h_goto` 自动追加 `page.wait_for_load_state("networkidle")`
- [x] 3.2 `_h_expect` 支持 `state` 参数（visible/hidden/enabled/disabled/editable）
- [x] 3.3 新增 `_h_wait_for_load_state` handler（domcontentloaded/load/networkidle）

## 4. 前端类型更新

- [x] 4.1 `step.ts` 新增 `wait_for_load_state` action
- [x] 4.2 `step.ts` expect 新增 `state` 下拉参数

## 5. 验证

- [x] 5.1 12/12 单元测试全部通过
- [x] 5.2 生成脚本语法验证通过
- [x] 5.3 所有选择器类型消歧输出验证通过
