## 上下文

Suite 模型已包含 `created_at` 字段（DateTime, server_default=func.now()），后端 `SuiteOut` Schema 已返回该字段。前端 `Suite` 接口也已包含 `created_at: string`。当前 Suites.vue 表格有 5 列（序号/系统名称/版本号/描述/操作），缺少创建日期展示。

## 目标 / 非目标

**目标：**
- 在系统用例列表表格中新增"系统创建日期"列，位于"描述"列右侧

**非目标：**
- 不修改后端 Schema 或 API
- 不修改编辑/新增弹窗

## 决策

1. **日期格式化**：在后端返回 ISO 8601 字符串的基础上，前端使用 `new Date().toLocaleString('zh-CN')` 本地化显示
2. **列宽**：使用 `min-width="160"` 与其他列保持一致的平均分布策略
3. **列对齐**：`align="center"` 与其他内容列保持一致

## 风险 / 权衡

- 无风险，纯前端展示变更
