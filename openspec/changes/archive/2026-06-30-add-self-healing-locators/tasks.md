## 1. 自愈辅助函数模板

- [x] 1.1 新增 `_SAFE_HELPER` 常量，定义 `_safe(page, strategies)` 函数模板（与 `_OVERLAY_HELPER` 同级）
- [x] 1.2 在 `generate_script()` 中：有交互步骤时注入 `_safe()` 定义（仿照 `_dismiss_overlays` 注入模式）
- [x] 1.3 在 `generate_script()` 初始 `_dismiss_overlays` 调用前插入 `_safe()` 定义行

## 2. 备选策略推导函数

- [x] 2.1 新增 `_build_fallbacks(sel: str) -> list[str]` 函数，接收原始 selector，返回 Playwright 引擎选择器策略列表
- [x] 2.2 实现语义选择器推导：`__role:` → text 备选；`__text:` → aria-label + button:has-text 备选；`__label:` → placeholder + input[name] 备选；`__placeholder:` → input[placeholder*=] 备选
- [x] 2.3 实现 CSS 选择器推导：含 `:has-text()` → 提取 text 生成 text/role 备选；纯 id 选择器 → 无备选；class 选择器 → 提取关键词生成 text/role 备选
- [x] 2.4 实现保守过滤：纯数字/过短关键词不推导；XPath/alt/title 不推导；testid 不推导

## 3. 生成代码中的策略列表构造

- [x] 3.1 新增辅助函数 `_safe_locator_code(p: dict) -> str`，返回 `_safe(page, [...strategies])` 代码片段或退化回原始 `_locator(sel)`
- [x] 3.2 修改 `_h_click`：当备选策略 >1 时使用 `_safe()` 包装，否则保持原样
- [x] 3.3 修改 `_h_fill`：同上
- [x] 3.4 修改 `_h_check`、`_h_uncheck`、`_h_select`、`_h_hover`：同上

## 4. 验证

- [x] 4.1 运行 `pytest backend/tests/ -v --tb=short` 确保现有 12 个单元测试通过
- [x] 4.2 检查生成脚本包含 `_safe()` 定义及正确的策略列表代码
- [x] 4.3 检查纯导航用例不会注入 `_safe()` 定义
- [x] 4.4 检查 CSS 选择器步骤退化为原始 `locator().click()` 格式
