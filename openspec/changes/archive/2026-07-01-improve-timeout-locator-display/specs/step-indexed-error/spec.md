## 新增需求

### 需求:错误信息中包含失败步骤索引
回放失败时，`_parse_playback_error()` 返回的 `error_info` 必须包含失败步骤的索引和对应的定位器。

#### 场景:通过标记定位失败步骤
- **当** 回放因 locator 超时而失败
- **那么** 系统在 stdout 中查找最后一个 `__STEP_MARKER__:{i}` 标记
- **那么** 通过标记中的步骤索引 i 在原始 steps 列表中查找对应的定位器
- **那么** `error_info.step_index` 返回步骤索引
- **那么** `error_info.locator` 返回该步骤的 selector

#### 场景:没有标记时回退旧逻辑
- **当** stdout 中没有 `__STEP_MARKER__` 标记（旧版本生成的脚本）
- **那么** 回退到 `_extract_locator_from_context()` 的文本回溯搜索方式
- **那么** `step_index` 不返回
