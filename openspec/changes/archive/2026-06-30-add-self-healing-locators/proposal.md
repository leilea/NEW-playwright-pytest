## 为什么

录制生成的 Playwright 脚本从 Codegen 只拿到一个 CSS 选择器（如 `.el-button--primary:has-text("确定")`），页面改版后选择器失效，回放直接崩溃。此前引入的 `pytest-breadcrumb` 作为外置自愈方案已被移除（跨平台兼容性问题、属性冲突）。需要内置一套零外部依赖的自愈方案，让录制脚本跨页面改版依然存活。

## 变更内容

- 在 `script_gen.py` 中为生成的 Playwright 脚本注入 `_safe(page, strategies)` 自愈辅助函数
- 从现有 8 种语义化选择器类型自动推导 2-5 个备选降级策略
- 修改 `_h_click`、`_h_fill`、`_h_check`、`_h_select`、`_h_hover`、`_h_uncheck` 六个 handler，在备选策略 >1 个时使用 `_safe()` 包装
- 备选策略使用短超时避免总等待时间膨胀，最终策略保留正常超时以保证报错清晰

## 功能 (Capabilities)

### 新增功能
- `self-healing-locators`: 生成脚本中自动注入多策略级联定位 + 失败自动降级
- `script-gen-sel-fallbacks`: 脚本生成器自动从单 CSS 选择器推导备选语义化定位器

### 修改功能
- `script-generation`: 6 个 action handler 在生成代码时可选地使用 `_safe()` 包装替代直接 `locator().click()`

## 影响

- 仅修改 `backend/app/services/script_gen.py`（~80 行新增/修改）
- 不修改 API、数据库、前端、录制器、回放引擎
- 现有测试保持兼容：备选策略为空或仅 1 个时退化回原生 `locator().action()`
