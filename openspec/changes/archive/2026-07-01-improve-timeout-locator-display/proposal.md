## 为什么

当前回放失败时，`_parse_playback_error()` 依赖 `_extract_locator_from_context()` 通过**回溯正则搜索**从错误文本中猜测失败定位器。这种方式不可靠：多步骤脚本中可能定位到错误步骤之前的调用，800字符窗口可能失效，且无法关联到具体是第几步失败。结果页显示"未知定位器"或内部格式字符串，用户无法快速定位到出错的步骤和元素。

已有 spec（`playback-error-prompt`）要求"显示失败定位器和对应步骤序号"，但实现未满足此需求。

## 变更内容

- 在脚本生成时植入 `__STEP_MARKER__` 打印标记，精确标识每个步骤的序号
- 修改错误解析逻辑，通过标记直接定位失败步骤，不再依赖回溯文本搜索
- 错误信息中返回 `step_index`，前端展示步骤序号 + 操作类型 + 定位器

## 功能 (Capabilities)

### 新增功能
- `step-marker-injection`: 在生成的回放脚本中，每步操作前注入带步骤序号的打印标记
- `step-indexed-error`: 错误信息中携带步骤索引，前端按步骤序号展示失败位置

### 修改功能
- `playback-error-prompt`: 补齐"显示失败定位器和对应步骤序号"的实现缺口

## 影响

- `backend/app/services/script_gen.py` — 增加步骤标记打印
- `backend/app/services/playback.py` — 解析步骤标记，返回 step_index
- `frontend/src/types/index.ts` — PlaybackErrorInfo 增加 step_index 字段
- `frontend/src/pages/CaseEditor.vue` — 错误卡片增加步骤序号展示
