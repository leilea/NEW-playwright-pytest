## 1. 后端：Playwright 错误解析

- [x] 1.1 在 `playback.py` 中新增 `_parse_playback_error(stdout: str, stderr: str) -> dict` 函数，先解析 stderr 再解析 stdout
- [x] 1.2 实现 `timeout` 类型匹配：正则 `Locator\.(\w+):.*Timeout (\d+)ms exceeded`，向前搜索 selector/locator 表达式
- [x] 1.3 实现 `strict_violation` 类型匹配：正则 `strict mode violation: locator\((.+?)\) resolved to (\d+) elements`，提取 selector 和元素列表
- [x] 1.4 实现 `load_state_timeout` 类型匹配：正则 `wait_for_load_state.*Timeout (\d+)ms exceeded`，提取 state 类型
- [x] 1.5 实现 `assertion` 类型匹配：正则 `expect\((.+?)\)\.to_(.+?)\(\)` 或 `AssertionError` 关键词
- [x] 1.6 在 `run_playback()` 返回值中增加 `error_info` 字段，透传到 WS 响应

## 2. 前端：类型定义

- [x] 2.1 在 `types/index.ts` 中新增 `PlaybackErrorInfo` 接口，包含 `type`、`locator`、`detail`、`timeout_ms`、`elements`、`expected_state` 等字段
- [x] 2.2 更新 `CaseEditor.vue` 中 `playbackResult` 的类型，增加 `error_info?: PlaybackErrorInfo`

## 3. 前端：中文错误提示 UI

- [x] 3.1 在"回放结果" tab 中，当 `playbackResult.error_info` 存在时，在 `el-alert` 下方渲染结构化错误卡片
- [x] 3.2 根据 `error_info.type` 显示不同中文提示文本和 icon
- [x] 3.3 展示失败定位器（`<code>` 块）、匹配元素列表（strict violation 时）、步骤序号
- [x] 3.4 将原始 stdout/stderr 改为 `el-collapse` 可折叠展示，默认收起

## 4. 验证

- [x] 4.1 后端：运行单元测试验证 `_parse_playback_error()` 覆盖 4 种错误类型 + 无匹配时的 fallback
- [x] 4.2 前端：手动验证回放失败时结构化提示正常展示（vue-tsc --noEmit 通过）
