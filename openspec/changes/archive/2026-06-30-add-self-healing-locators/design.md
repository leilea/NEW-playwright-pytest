## 上下文

`script_gen.py` 是脚本生成层，负责将录制步骤（action + params）转换为可执行的 pytest Playwright 代码。当前 6 个交互 handler（`_h_click` 等）直接生成 `page.locator(selector).action()` —— 如果录制到的 CSS 选择器在产品改版后失效，脚本直接崩溃。

此前 `pytest-breadcrumb` 外置包提供了指纹级别的自愈，但已被移除。现需内置零外部依赖的降级方案。

## 目标 / 非目标

**目标：**
- 生成脚本中每个交互动作携带 2-5 个备选定位器，按优先级级联尝试
- 备选定位器从现有选择器自动推导，无需人工标注
- 当选择器只有 1 个有效策略时，退化为原生行为，零开销

**非目标：**
- 不修改录制器、回放引擎、API、前端
- 不缓存/学习成功的定位器（不做运行时状态追踪）
- 不对 `expect` 断言或 `goto`/`screenshot` 等非交互动作做自愈

## 决策

### 决策 1：注入 helper 函数模板，而非运行时 monkey-patch

**选择**：在生成脚本中注入 `_safe(page, strategies)` 函数定义（类似现有 `_dismiss_overlays`）。

**替代方案**：在回放子进程内 monkey-patch `page.locator`。不选的原因：子进程环境不可控，且无法生成可独立运行的脚本。

### 决策 2：推导在生成时而非录制时

**选择**：保持录制器不修改，在 `script_gen.py` 中从已有 selector 字符串推导备选。

**替代方案**：录制时通过 Codegen 漏出更多元素属性。不选的原因：Codegen 输出不可控，修改录制器增加耦合。

**推导表**：

| 主选择器模式 | 降级链 (按优先级) |
|---|---|
| `__role:button:登录` | `get_by_role("button", name="登录")` → `get_by_text("登录")` |
| `__text:提交` | `get_by_text("提交")` → `get_by_role("button", name="提交")` → `locator("text=提交")` |
| `__label:用户名` | `get_by_label("用户名")` → `get_by_placeholder("请输入用户名")` → `locator("input[name=用户名]")` |
| `__placeholder:搜索` | `get_by_placeholder("搜索")` → `locator("input[placeholder*=搜索]")` |
| `__testid:login-btn` | `get_by_test_id("login-btn")` → `locator("[data-testid=login-btn]")` |
| CSS `#loginBtn` | `locator("#loginBtn")` → `get_by_text("登录")` → `get_by_role("button", name="登录")` (text 从 id/class 推导) |
| CSS `.el-btn:has-text("确定")` | 原 CSS → `get_by_text("确定")` → `get_by_role("button", name="确定")` |
| 纯 CSS 无 :has-text | `locator(css)` → 从 class/id 提取关键词 → text/role 备选 |
| `__xpath:` / `__alt:` / `__title:` | 仅原选择器，不推导（XPath 本身已是兜底） |

### 决策 3：分级超时避免惩罚

`_safe()` 对前 N-1 个策略用 `count()` 检查（不触发 actionability 等待），最后一个策略使用原生 Playwright 行为（正常超时 + 完整错误信息）。

```python
def _safe(page, strategies):
    for sel, timeout in strategies[:-1]:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                return page.locator(sel)
        except Exception:
            continue
    return page.locator(strategies[-1][0])  # 最后一个让 Playwright 报原生错误
```

### 决策 4：生成代码结构

- `_safe()` 函数定义只在有交互步骤时注入一次，模板常量 `_SAFE_HELPER`
- handler 只负责构造 `strategies` 列表并生成 `_safe(page, strategies).action()` 调用
- 当 `strategies` 长度为 1 时（如 XPath），退化为直接 `locator().action()`，零开销

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|---------|
| 备选选择器命中错误元素（同名文本的不同按钮） | 优先 `role+name` 精确匹配；`text` 备选只在 role 失败后使用 |
| 推导的文本关键词不准确（class 名 → 文本映射无意义） | 仅当 class/id 包含有意义词汇（至少 2 个字符或中文）时才生成 text/role 备选 |
| 增加脚本体积 | 每个交互动作增加 ~2 行，可接受 |
| `count()` 在动态加载页面不准确 | `count()` 仅做"是否存在"快速判断，不依赖其精度 |

## 开放问题

- 是否需要生成自愈日志（`print` 降级记录）？—— 首版不包含，后续按需添加
- 是否需要降级策略持久化（记录哪个备选策略成功了）？—— 首版不包含，每次重新推导
