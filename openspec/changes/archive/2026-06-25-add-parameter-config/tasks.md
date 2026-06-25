## 1. 数据库迁移

- [x] 1.1 创建 Alembic 迁移 `0003_add_parameters_to_cases.py`，为 `catalog.cases` 添加 `parameters` JSON 列

## 2. 后端数据模型

- [x] 2.1 在 `backend/app/models/catalog.py` Case 模型添加 `parameters = Column(JSON, default=list)`
- [x] 2.2 在 `backend/app/schemas/catalog.py` CaseIn 和 CaseOut 添加 `parameters: list[dict]` 字段

## 3. 后端业务逻辑

- [x] 3.1 修改 `backend/app/services/case_service.py`：`create_case` 和 `update_case_steps` 支持 `parameters` 参数
- [x] 3.2 修改 `backend/app/routers/cases.py`：创建和更新接口透传 `parameters`
- [x] 3.3 在 `backend/app/services/script_gen.py` 实现 `replace_params()` 参数替换引擎
- [x] 3.4 修改 `generate_script()` 和路由中的脚本接口，支持参数替换

## 4. 前端类型定义

- [x] 4.1 在 `frontend/src/types/index.ts` 新增 `Parameter` 接口，`Case` 类型增加 `parameters` 字段

## 5. 前端参数配置组件

- [x] 5.1 创建 `frontend/src/components/ParameterConfig.vue` 组件框架（标题、提示语、添加按钮）
- [x] 5.2 实现参数列表渲染（参数名输入框、参数值输入框、描述输入框、删除按钮）
- [x] 5.3 实现动态值类型下拉菜单（10 种类型，使用 Element Plus icons）
- [x] 5.4 实现偏移量设置弹窗（针对 timeAdd/timeSub/dateAdd/dateSub 四种类型）
- [x] 5.5 实现空列表提示状态

## 6. 前端集成

- [x] 6.1 在 `CaseEditor.vue` 中集成 `ParameterConfig` 组件（插入在表单和 Tabs 之间）
- [x] 6.2 更新 `save()` 方法，将 `parameters` 加入请求体
- [x] 6.3 更新 `playback()` 方法，回放前用前端 JS 执行参数替换
- [x] 6.4 加载已有用例时回填 `parameters` 到表单

## 7. 验证

- [x] 7.1 运行后端测试验证迁移和 API
- [x] 7.2 运行前端构建验证无类型错误
