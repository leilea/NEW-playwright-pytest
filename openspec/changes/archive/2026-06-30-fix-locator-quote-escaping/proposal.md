## 为什么

用户编辑步骤定位器并保存后，"操作步骤"页面显示的定位器字符串中，CSS 属性选择器内的双引号被 `\"` 转义显示，视觉上造成困惑。例如输入 `locator("[data-field-id="purch_demand_name"]")` 保存后显示为 `locator("[data-field-id=\"purch_demand_name\"]")`。

**根因**: `_q()` 函数 (locator.ts:83) 使用 `JSON.stringify()` 包裹值，永远用双引号且转义内部 `"` 为 `\"`。当 CSS 选择器含 `[attr="val"]` 时会产生视觉转义。

## 变更内容

- 修改 `_q()` 函数：当值含 `"` 但不含 `'` 时，优先用单引号包裹，避免 `\"` 转义
- 当值同时含 `"` 和 `'` 时，回退到 `JSON.stringify()` 进行转义

## 功能 (Capabilities)

### 新增功能
- `locator-display`: 定位器在操作步骤页面上的显示格式应尽量减少视觉转义

### 修改功能
<!-- 无 -->

## 影响

- `frontend/src/utils/locator.ts` — `_q()` 函数
