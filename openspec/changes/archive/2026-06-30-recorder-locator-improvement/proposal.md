## 为什么

录制生成的定位器在 Element Plus 等 UI 框架下退化为不唯一的 `get_by_placeholder("请输入")`，导致回放失败。原因是 `_findLabel()` 仅支持原生 `<label for>` 关联，而 Element Plus 使用 `.el-form-item__label` 无语义关联；同时裸角色定位器（`__role:textbox`）被无条件标记为唯一，跳过了更精确的 CSS/id 回退。

## 变更内容

1. **增强标签发现**：`_findLabel()` 新增 `.el-form-item__label` 检测，支持 Element Plus 等 UI 框架
2. **修复伪唯一性 bug**：`__role:role`（裸角色）不再无条件标记 unique，改为检查实际匹配数
3. **增强父级上下文**：`_findParentContext()` 新增对 `.el-form-item` 等框架容器的自动 id 回退

## 功能 (Capabilities)

### 新增功能
<!-- 无新增功能，全部为现有定位器策略的增强 -->

### 修改功能
- `recorder-locator-strategy`: 增强标签发现逻辑和唯一性判断；裸角色定位器不再无条件标记为唯一

## 影响

- `backend/app/services/recorder_process.py` — `RECORDER_INJECT_JS` 中 `_findLabel()`、`_findParentContext()` 函数及 `__role:role` 候选逻辑
- 现有已录制的用例不受影响（定位器已写入存储），仅新录制生效
