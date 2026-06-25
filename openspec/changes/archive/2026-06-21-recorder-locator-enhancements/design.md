## 上下文

`recorder_process.py` 的 `genSelector()` 当前生成 CSS 选择器（class 优先），`script_gen.py` 直接使用 `page.locator(css)`。CSS class 和 `:has-text()` 非常脆弱。此外 goto 后无等待，expect 仅支持 visible。

## 目标 / 非目标

**目标：**
- `genSelector` 优先语义定位：label → placeholder → role+name → text → data-testid → CSS id → name → tag
- `_locator()` 转换前缀为 Playwright API：`__label:`, `__placeholder:`, `__role:`, `__text:`, `__testid:`
- 所有语义选择器追加 `|tag` 后缀消除歧义
- goto 后自动 `wait_for_load_state("networkidle")`
- expect 支持 hidden/enabled/disabled/editable 状态

**非目标：**
- 不改动录制 WS 协议
- 不改动前端 RecorderPanel

## 决策

### 决策 1：语义选择器优先级

**采用**：label(with for/aria-labelledby) > label(text) > aria-label > role+name > text(content/strict) > placeholder > role-only > data-testid > CSS id > name > tag。

**理由**：Playwright 推荐 get_by_role/get_by_label 的可靠性远超 CSS class 选择器。文本匹配用 exact=True 避免部分匹配。

### 决策 2：通用 |tag 消歧而非唯一性检查

**采用**：所有语义选择器生成时调用 `_scope()` 追加 `|tag` 后缀（`__text:登录|a`），`_locator()` 解析为 `page.locator("a").filter(has=page.get_by_text("登录"))`。

**理由**：唯一性检查是 O(n) 开销且不能保证跨页面一致性。|tag 方案轻量通用。

### 决策 3：goto 后自动等待

**采用**：`_h_goto` 自动追加 `page.wait_for_load_state("networkidle")`。

**理由**：导航后立刻操作元素是回放失败的头号原因。networkidle 最保守。

## 风险 / 权衡

- **[风险]** get_by_text exact=True 匹配标点差异 → 缓解：`|tag` 限定缩小范围
- **[风险]** get_by_role 语义不匹配 → 缓解：`_inferRole()` 用 tag→role 映射，非标准 role 降级到 text 定位
