## 1. 后端 — 脚本生成植入步骤标记

- [x] 1.1 在 `script_gen.py` 的 `generate_script()` 中，迭代每个步骤时，在 handler 行之前添加 `print(f"__STEP_MARKER__:{i}")`
- [x] 1.2 考虑导航型 click（被 `with expect_navigation` 包裹）的标记位置：标记放在 `with` 块之前

## 2. 后端 — 错误解析获取步骤索引

- [x] 2.1 修改 `_parse_playback_error()` 签名，增加可选参数 `steps: list[dict] | None = None`
- [x] 2.2 在 timeout 分支中，从 stdout 搜索最后一个 `__STEP_MARKER__:(\d+)` 并提取 `step_index`
- [x] 2.3 通过 `step_index` 在 `steps` 列表中查找 `action` 和 `selector`，构建精确的 `error_info`
- [x] 2.4 在 `error_info` 中返回 `step_index` 字段
- [x] 2.5 `run_playback()` 中调用 `_parse_playback_error()` 时传入 `steps`
- [x] 2.6 没有标记时保持向后兼容，回退到 `_extract_locator_from_context()`

## 3. 前端 — 类型定义扩展

- [x] 3.1 在 `types/index.ts` 的 `PlaybackErrorInfo` 接口中增加 `step_index?: number`

## 4. 前端 — 错误卡片增强

- [x] 4.1 `CaseEditor.vue` 的 error-card 头部增加步骤序号标签 `el-tag`（"第 N 步"）
- [x] 4.2 将 `detail` 中的动作类型改为更清晰的语言："第 {step_index+1} 步 [{action}] 定位元素超时"
- [x] 4.3 定位器行改为始终显示，为空时显示占位符"（未获取到定位器信息）"
