## 上下文

`frontend/src/utils/locator.ts` 中的 `_q()` 函数负责将定位器的值包裹为 Playwright 可用的字符串字面量。当前实现：

```ts
function _q(v: string): string {
  return JSON.stringify(v)
}
```

`JSON.stringify()` 永远使用双引号，内部 `"` 被转义为 `\"`。当 CSS 选择器含 `[attr="val"]` 时，`selectorToLocator()` 产生的显示字符串形如 `page.locator("[data-field-id=\"purch_demand_name\"]")`，视觉上有 `\"` 转义。

Python 端的 `_quote()` (script_gen.py:427) 使用 `repr()`，能自动选择单引号或双引号，所以脚本生成不受影响 — 这是纯前端的显示问题。

## 目标 / 非目标

**目标：**
- `_q()` 产生的定位器字符串尽可能减少转义字符，优先使用与值不冲突的引号

**非目标：**
- 不修改后端 `_quote()` 函数（Python `repr()` 已正确处理）
- 不修改 `_unquote()` 解析逻辑

## 决策

**选择方案 A**: 在 `_q()` 中判断值内容，选择合适引号类型

```ts
function _q(v: string): string {
  if (v.includes('"') && !v.includes("'")) return "'" + v + "'"
  if (v.includes("'") && !v.includes('"')) return '"' + v + '"'
  return JSON.stringify(v)
}
```

- 值含 `"` 无 `'` → 用单引号（最常见场景，如 CSS `[attr="val"]`）
- 值含 `'` 无 `"` → 用双引号
- 值同时含两者 → `JSON.stringify()` 回退（少数情况）

**替代方案 B**: 始终用单引号 → 被否决，因为值可能含单引号

## 风险 / 权衡

- [风险] 值含 `'` 时切换为双引号，但 Playwright 端对双引号的支持与单引号完全一致 → 无风险
- [风险] 同时含 `"` 和 `'` 时回退，仍显示转义 → 可接受的边界情况
