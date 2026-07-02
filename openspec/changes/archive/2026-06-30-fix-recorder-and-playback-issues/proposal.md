## 为什么

回放脚本时有 2 个阻断性问题：(1) 对话框遮罩拦截点击导致 54 次重试后 TimeoutError；(2) 新版 Playwright Codegen (>=1.50) 输出的 `page.get_by_*()` 格式无法被录制端正确解析，导致 textarea 的 fill 动作丢失。这两个问题使录制→回放流程不可用，需立即修复。

## 变更内容

1. **录制端** (`recorder.py`): 更新正则解析器以支持 Playwright Codegen 新格式 (`get_by_placeholder`, `get_by_role`, `get_by_label`, `get_by_text`, `get_by_test_id` 等链式调用)
2. **脚本生成端** (`script_gen.py`): 为交互动作（click/fill/hover/check/select）添加弹窗遮罩检测，被拦截时自动关闭弹窗后重试
3. 修复解析器中双引号转义的边界情况

## 功能 (Capabilities)

### 新增功能
- `recorder-get-by-parsing`: 录制端正确解析 Playwright Codegen 的 `page.get_by_*()` 链式调用格式，包括 `get_by_placeholder`, `get_by_role`, `get_by_label`, `get_by_text`, `get_by_test_id`, `get_by_alt_text`, `get_by_title`
- `playback-overlay-dismiss`: 回放时自动检测并关闭遮挡对话框/遮罩 (`comp_dialog_warp` 等)，避免元素点击被拦截超时

### 修改功能
<!-- 无需修改现有规范 -->

## 影响

- `backend/app/services/recorder.py`: STEP_PATTERNS 正则表扩展，parse_codegen_line 增加方法分支
- `backend/app/services/script_gen.py`: _h_click/_h_fill/_h_check/_h_select/_h_hover 方法增加 overlay dismiss 逻辑
- `backend/app/services/playback.py`: 错误解析增加 overlay 拦截类别
