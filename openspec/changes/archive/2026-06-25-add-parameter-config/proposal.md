## 为什么

测试用例中的操作步骤通常需要参数化——例如用户名、密码、日期等值不应硬编码在步骤中，而应在执行时动态注入。当前系统缺少参数化机制，导致同一用例无法适应不同环境或数据。此变更引入参数配置功能，允许用户为每个测试用例定义一组键值对参数，在脚本生成和回放时自动替换占位符。

## 变更内容

- **新增**: 测试用例详情页新增「参数配置」区域，支持添加/修改/删除参数行
- **新增**: 参数值支持 10 种动态类型选择（随机数字、随机字符串、当前日期、当前时间、日期时间、时间戳、时间±N小时、日期±N天），其中 4 种支持偏移量设置
- **新增**: 参数占位符替换引擎，在脚本生成和回放时自动将 `{{paramName}}` 替换为实际值
- **新增**: 数据库 `catalog.cases` 表新增 `parameters` JSON 列存储参数数据
- **修改**: 后端 API 创建/更新/脚本接口透传 parameters 字段

## 功能 (Capabilities)

### 新增功能
- `case-parameter-config`: 测试用例参数配置功能——用户可为用例定义键值对参数，支持动态类型选择和偏移量设置，参数值在脚本生成和回放时通过占位符替换引擎自动注入

### 修改功能
- `case-editor-script-sync`: 脚本生成逻辑新增参数替换阶段，生成脚本前将步骤值中的占位符替换为实际参数值

## 影响

- **前端**: `CaseEditor.vue` 页面新增 `ParameterConfig.vue` 组件，`types/index.ts` 新增 `Parameter` 接口
- **后端**: `models/catalog.py`、`schemas/catalog.py`、`services/case_service.py`、`services/script_gen.py`、`routers/cases.py` 均需修改
- **数据库**: 新增 Alembic 迁移 `0003_add_parameters_to_cases.py`
- **API**: `CaseIn`/`CaseOut` schema 新增 `parameters` 字段，脚本生成接口增加参数替换逻辑
