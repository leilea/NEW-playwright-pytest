## 1. 录制端 - 归一化函数

- [x] 1.1 在 `recorder.py` 中新增 `_normalize_codegen_line` 函数，将 `page.get_by_*(...).action()` 转换为 `page.locator("__prefix:arg").action()` 格式
- [x] 1.2 在 `parse_codegen_line` 开头调用归一化函数
- [x] 1.3 归一化支持的 get_by_* 映射: get_by_placeholder, get_by_role, get_by_label, get_by_text, get_by_test_id, get_by_alt_text, get_by_title
- [x] 1.4 确保归一化后仍正确解析原有 page.locator 和 page.fill 格式（向后兼容）

## 2. 录制端 - 正则适配

- [x] 2.1 因归一化已将 get_by_* 转为 locator 格式，确认现有 STEP_PATTERNS 无需修改
- [x] 2.2 适配 click 模式匹配 `.click()` 后可能跟随的 `.first`, `.nth(N)` 等过滤方法（如有必要）

## 3. 回放端 - 遮罩处理辅助函数

- [x] 3.1 在 `script_gen.py` 中新增 OVERLAY_SELECTORS 常量列表，包含主流 UI 库遮罩类名
- [x] 3.2 新增 `_dismiss_overlays_text` 生成函数，输出注入到脚本中的 `_dismiss_overlays(page)` 辅助函数代码
- [x] 3.3 修改 `generate_script` 函数，在脚本中注入 `_dismiss_overlays` 辅助函数定义并在测试函数内调用
- [x] 3.4 在 `generate_script` 循环中，每个交互动作（click/fill/hover/check/uncheck/select）前加入 `_dismiss_overlays(page)` 调用

## 4. 回放端 - 错误解析增强

- [x] 4.1 在 `playback.py` 的 `_parse_playback_error` 中增加 overlay 拦截错误识别（检测 "intercepts pointer events" 关键字）
- [x] 4.2 overlay 拦截错误输出友好的错误信息："元素被弹窗遮罩遮挡，请检查弹窗是否关闭"

## 5. 验证

- [x] 5.1 单元测试 `_normalize_codegen_line` 对各种 get_by_* 格式的解析正确性
- [x] 5.2 单元测试归一化后的 `parse_codegen_line` 向后兼容原有格式
- [x] 5.3 验证生成的脚本包含 `_dismiss_overlays` 辅助函数且交互动作前有调用
- [x] 5.4 运行项目现有测试（12/12 通过）确保无回归
