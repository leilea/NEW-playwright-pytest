## 为什么

在测试用例详情页的"操作步骤"标签页中编辑步骤（复制、删除、上移/下移等）并点击【保存】后，数据库已更新，但"生成脚本"标签页仍显示保存前的旧脚本内容。这是因为 `save()` 函数在 PUT 成功后没有刷新脚本内容。

## 变更内容

- 在 `CaseEditor.vue` 的 `save()` 函数中，PUT 成功后调用 `loadScript()` 刷新"生成脚本"标签页

## 功能 (Capabilities)

### 新增功能

- `case-editor-script-sync`: 保存操作步骤后自动刷新生成脚本标签页，确保显示的脚本内容与数据库中最新的步骤数据一致

### 修改功能

<!-- 无现有规范层面的需求变更 -->

## 影响

- `frontend/src/pages/CaseEditor.vue`: `save()` 函数增加 `loadScript()` 调用
