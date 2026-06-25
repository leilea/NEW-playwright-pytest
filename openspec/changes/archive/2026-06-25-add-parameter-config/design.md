## 上下文

当前 `CaseEditor.vue` 页面布局为：表单区（名称/套件）→ 三个 Tab（操作步骤、生成脚本、回放结果）。参数配置功能将插入在表单区和 Tab 区之间，作为独立区域展示。后端 `Case` 模型已有 `steps` JSON 列存储步骤，参数采用相同的 JSON 列策略存储。

参考文档 `CS配置.txt` 描述了 React 版本的完整实现，本设计将其适配到 Vue 3 + Element Plus 技术栈。

## 目标 / 非目标

**目标：**
- 在 `CaseEditor.vue` 中新增参数配置区域，位于表单区和 Tabs 之间
- 参数持久化存储到数据库 `catalog.cases.parameters` JSON 列
- 用户可添加/修改/删除参数行（3 列：参数名、参数值、描述）
- 参数值列提供 10 种动态类型选择下拉菜单和偏移量弹窗
- 脚本生成和回放时自动替换 `{{paramName}}` 占位符
- 回放时在前端完成参数替换后发送给 WebSocket

**非目标：**
- 不在套件级别支持参数配置（仅用例级别）
- 不实现参数导入导出功能
- 不实现参数批量编辑
- 不修改 vxe-table StepEditor 的内部结构

## 决策

### 1. 参数存储策略：JSON 列
- **决策**: 使用 SQLAlchemy `JSON` 列存储 `parameters: [{key, value, description}]`
- **理由**: 与现有 `steps` 列保持一致；JSON 灵活支持动态表单；无需额外关联表
- **替代方案**: 独立 `case_parameters` 关联表 — 过度设计，参数数量少且结构简单

### 2. 前端组件拆分：新建 `ParameterConfig.vue`
- **决策**: 创建独立组件 `ParameterConfig.vue`，通过 `v-model` 与 CaseEditor 通信
- **理由**: 关注点分离；CaseEditor 已包含较多逻辑；便于后续复用
- **替代方案**: 内联在 CaseEditor 中 — 会使文件过于膨胀

### 3. 参数替换时机：脚本生成→后端，回放→前端
- **决策**: 
  - 脚本标签页：后端 `GET /api/cases/{id}/script` 在生成脚本前替换参数
  - 回放：前端 `CaseEditor.playback()` 发送 WebSocket 前用 JS 替换参数
- **理由**: 脚本生成需要 DB 中的参数数据（后端持有）；回放时前端已持有参数，避免额外传参
- **替代方案**: 全部在单侧完成 — 后端替换需额外传参，前端替换需加载参数后二次请求

### 4. 动态值类型实现
- **决策**: 使用 `el-dropdown` 实现类型选择菜单，使用 `el-dialog` 实现偏移量弹窗
- **理由**: Element Plus 原生组件，无需额外依赖；与项目风格一致
- **替代方案**: 自定义弹出层 — 重复造轮子

### 5. 前端图标选择
- **决策**: 使用 `@element-plus/icons-vue` 中的 `Calendar`、`Clock`、`Key`、`Edit`、`Delete`、`MagicStick`
- **理由**: 项目已安装此图标库，无需额外依赖

## 风险 / 权衡

- **[数据一致性]**: 前端 `form.parameters` 和后端 `case.parameters` 可能不同步 → 缓解：保存时整体 PUT 覆盖，加载时整体 GET 回填
- **[SQLite JSON 兼容]**: SQLite 对 JSON 列支持有限 → 缓解：项目使用 PostgreSQL，JSON 列原生支持良好
- **[参数替换顺序]**: 用户自定义参数 key 与内置占位符同名时可能冲突 → 缓解：自定义参数先替换，内置占位符后替换（参考文档行为）

## 迁移计划

1. 运行 Alembic 迁移为 `catalog.cases` 添加 `parameters` 列
2. 后端代码部署（新增列有默认值 `[]`，向后兼容）
3. 前端代码部署
4. 回滚：`downgrade` 迁移删除 `parameters` 列
