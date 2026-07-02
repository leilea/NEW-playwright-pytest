## 为什么

修改步骤定位器并保存后，页面仍显示旧定位器。根因是 `StepEditor.vue` 中 `deep: true` 的 watch 无条件清空 `editCache`，导致用户正在编辑的定位值被任何步骤属性变化触发丢失；同时 `CaseEditor.vue` 的 `save()` 丢弃了 API 返回值，保存后未刷新前端数据。

## 变更内容

1. `StepEditor.vue`: `editCache` 维护逻辑改为增量更新（只处理新增/删除步骤，保留已有编辑）
2. `CaseEditor.vue`: `save()` 使用 API 返回值刷新 `form.value.steps`

## 功能 (Capabilities)

### 修改功能
- `case-editor`: 步骤编辑器的定位器修改在保存时正确持久化并反映到页面显示

## 影响

- `frontend/src/components/StepEditor.vue` — watch 回调逻辑
- `frontend/src/pages/CaseEditor.vue` — save() 函数
