## 为什么

当前回放失败时，前端仅显示原始 pytest stdout/stderr，用户需要从堆栈中自行查找哪个元素定位失败及原因，体验差。需要在回放结果页直接给出中文提示，告诉用户哪个元素定位失败、失败原因。

## 变更内容

1. **后端**: 新增 `_parse_playback_error()` 函数，解析 pytest 输出中的 Playwright 错误信息，提取错误类型、定位器、步骤序号等结构化数据
2. **前端**: 在"回放结果" tab 增加结构化中文错误提示展示区域，覆盖超时、strict mode violation、networkidle 超时、断言失败等常见错误类型
3. **类型定义**: 新增 `PlaybackErrorInfo` 接口

## 功能 (Capabilities)

### 新增功能
- `playback-error-prompt`: 录制脚本回放失败后，在回放结果页用中文提示用户失败元素和原因

### 修改功能
_无需求变更_

## 影响

- `backend/app/services/playback.py`: 新增 `_parse_playback_error()` 函数，`run_playback()` 返回值增加 `error_info` 字段
- `frontend/src/pages/CaseEditor.vue`: 新增中文错误提示 UI，保留可折叠的原始日志
- `frontend/src/types/index.ts`: 新增 `PlaybackErrorInfo` 接口
