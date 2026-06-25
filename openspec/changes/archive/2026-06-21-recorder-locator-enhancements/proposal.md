## 为什么

录制的步骤回放时，CSS class 定位器和 :has-text() 选择器频繁因页面改版而失效。此外，goto 操作后未等待页面加载完成就执行后续步骤，导致不稳定。需要更智能的定位策略和等待机制。

## 变更内容

- **重写** `genSelector()`：优先语义定位（label/placeholder/role/testid/text），放弃脆弱 CSS class 定位
- **新增** `_locator()` 转换：将语义选择器前缀转换为 Playwright API（get_by_label / get_by_placeholder / get_by_role / get_by_test_id / get_by_text）
- **新增** 通用标签限定消歧：所有语义选择器追加 `|tag` 后缀，用 `page.locator(tag).filter(has=...)` 消除多个匹配元素的歧义
- **新增** goto 后自动追加 `page.wait_for_load_state("networkidle")`
- **新增** `expect` 支持状态参数（visible/hidden/enabled/disabled/editable）
- **新增** `wait_for_load_state` action 类型

## 功能 (Capabilities)

### 新增功能
- `recorder-locator-strategy`: 基于语义属性的选择器生成策略语义标签限定消歧机制

### 修改功能
- `case-recording`: 选择器生成方式变更（放弃 CSS class，优先语义）；新增 `wait_for_load_state` action 类型；脚本生成 `_locator()` 转换
- `case-playback`: goto 步骤自动等待页面加载；expect 断言支持多种状态校验

## 影响

- **后端**：`recorder_process.py` 重写 `genSelector()`（新增 `_findLabel()`、`_inferRole()`、`_scope()`）；`script_gen.py` 新增 `_locator()`/`_raw_locator()`，所有 handler 改用链式调用；`expect` handler 新增 `state` 参数支持隐藏/启用等
- **前端**：`step.ts` 新增 `wait_for_load_state` action、`expect` 的 `state` 下拉参数
- **破坏性**：旧录制步骤的 CSS class 选择器不再生成，旧数据兼容但失去最优语义；旧脚本需重新生成
