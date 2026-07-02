## 上下文

本项目的录制→回放流程：
1. `recorder.py` 启动 `playwright codegen --target=python`，逐行解析输出为 {action, params} 结构
2. `script_gen.py` 将步骤列表转换为 pytest Playwright 测试脚本（含 `page.locator(...).click()` 等调用）
3. `playback.py` 执行生成的脚本并解析结果

存在两个链路问题：
- **录制端**：Codegen >=1.50 输出 `page.get_by_placeholder("请输入")` 格式，当前正则只匹配 `page.locator("x")` / `page.fill("x")`
- **回放端**：目标应用有 `comp_dialog_warp` 全屏遮罩，弹窗关闭步骤可能未被录制或弹窗由异步操作触发

## 目标 / 非目标

**目标：**
- 录制端正确解析 Codegen 输出的 `get_by_*` 链式调用格式
- 回放脚本自动处理对话框遮罩，避免点击被拦截超时

**非目标：**
- 不改变录制→回放的步骤数据格式（Step schema 保持不变）
- 不引入前端 UI 变更
- 不引入新的外部依赖

## 决策

### 决策 1: 录制正则改造——统一归一化 + 现有模式

**方案 A（选用）：** 在 `parse_codegen_line` 前增加 `_normalize_codegen_line` 归一化函数，将 `page.get_by_*(...).action()` 转换为 `page.locator("__prefix:arg").action()` 格式，然后复用现有 STEP_PATTERNS。

理由：不需要大幅修改现有解析逻辑，`script_gen.py` 已经支持 `__label:`、`__placeholder:` 等语义选择器前缀（通过 `_raw_locator`），前后统一。

归一化映射：
| Codegen 输出 | 归一化为 |
|---|---|
| `page.get_by_placeholder("p")` | `page.locator("__placeholder:p")` |
| `page.get_by_role("r", name="n", exact=True)` | `page.locator("__role:r:n")` |
| `page.get_by_label("l")` | `page.locator("__label:l")` |
| `page.get_by_text("t", exact=True)` | `page.locator("__text:t")` |
| `page.get_by_test_id("i")` | `page.locator("__testid:i")` |
| `page.get_by_alt_text("a")` | `page.locator("__alt:a")` |
| `page.get_by_title("t")` | `page.locator("__title:t")` |

**方案 B（未选用）：** 为每种 get_by_* 变体分别添加新正则。会导致 STEP_PATTERNS 膨胀到 50+ 条目，且前后端映射不一致。

**方案 C（未选用）：** 直接使用 Codegen 的 `--target=json` 模式。Playwright Codegen 没有 JSON 输出模式。

### 决策 2: 回放遮罩处理——生成辅助函数

**方案 A（选用）：** 在生成的脚本中注入 `_dismiss_overlays(page)` 辅助函数，在每次交互前调用，检测并关闭常见对话框遮罩（`.comp_dialog_warp`, `.el-dialog__wrapper`, `.el-overlay` 等 Element Plus / 常见 UI 库的遮罩类名）。

```python
def _dismiss_overlays(page):
    for overlay_sel in OVERLAY_SELECTORS:
        overlay = page.locator(overlay_sel)
        if overlay.is_visible():
            close_btn = overlay.locator(".el-dialog__close, .el-message-box__headerbtn, .el-icon-close, [aria-label='Close']")
            if close_btn.is_visible():
                close_btn.click()
                page.wait_for_timeout(300)
```

**方案 B（未选用）：** 使用 `{ force: true }` 强行点击。风险：会点到弹窗内部元素而非背后的目标元素，行为不可预测。

**方案 C（未选用）：** 仅前端提示用户手动添加"关闭弹窗"步骤。不能自动化解决问题。

### 决策 3: OVERLAY_SELECTORS 可配置

遮罩选择器列表从常量提取到 `config/settings` 中，便于用户按目标应用调整：

```python
OVERLAY_SELECTORS: list[str] = [
    ".comp_dialog_warp",       # 本项目目标系统
    ".el-dialog__wrapper",     # Element Plus
    ".el-overlay",
    ".el-message-box__wrapper",
    ".ant-modal-wrap",         # Ant Design
    ".v-overlay",              # Vuetify
]
```

## 风险 / 权衡

- **归一化丢失参数顺序信息**: `get_by_role("button", name="OK", exact=True)` 被压平为 `__role:button:OK`，丢失了 `exact=True` 参数。需要保证回放脚本生成时，`_raw_locator` 生成的 `get_by_role` 调用包含 `exact=True`（当前已包含）
- **遮罩关闭可能失败**: 如果对话框没有标准关闭按钮（如自定义弹窗），`_dismiss_overlays` 会静默失败，后续交互仍会超时。需要通过页面特定遮罩类名覆盖 → 用户可在 OVERLAY_SELECTORS 配置中添加自定义规则
- **遮罩关闭的时序问题**: 关闭弹窗后可能需要等待动画结束，当前使用 `wait_for_timeout(300)` 硬等待，对于动画较长的场景可能不够 → 未来可改为等待弹窗 `is_hidden()`
