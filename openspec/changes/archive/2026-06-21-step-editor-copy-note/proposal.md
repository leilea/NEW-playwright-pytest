## 为什么

用户编辑测试步骤时，需要复制已有步骤快速创建类似操作，以及在步骤旁添加备注说明特定逻辑。

## 变更内容

- **新增** StepEditor 操作列的步骤复制按钮
- **新增** StepEditor 的备注(Notes)文本框列

## 功能 (Capabilities)

### 新增功能
- `step-copy`: 在步骤编辑器中复制已有步骤，新步骤插入被复制步骤下方并自动重新编号
- `step-note`: 在步骤编辑器中为每个步骤添加可编辑的备注文本

### 修改功能
- `suite-case-management`: 步骤编辑区新增复制和备注可编辑字段

## 影响

- **前端**：`StepEditor.vue` 新增 Ops 列复制按钮、Notes 列 vxe-input；`step.ts` 新增 `copyStep()` 函数、`note` 字段和 `Step` 接口拓展
- **后端**：无改动，`note` 由前端存储为步骤属性
