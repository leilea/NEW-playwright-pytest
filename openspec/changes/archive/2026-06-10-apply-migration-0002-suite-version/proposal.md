## 为什么

打开"系统用例"页面时后端报 500 错误：`column suites.version does not exist`。迁移 `0002_add_suite_version.py` 已创建但未应用到数据库，导致 ORM 查询的 `version` 列在 `catalog.suites` 表中不存在。

## 变更内容

执行遗漏的数据库迁移 `0002_add_suite_version`，向 `catalog.suites` 表添加 `version` 列。

## 功能 (Capabilities)

### 新增功能
- `suite-version-column`: 确保 suite 表中存在 version 列，使系统用例页面可正常加载

### 修改功能

无

## 影响

- `backend/`: 仅需执行一次 alembic upgrade head，无需代码变更
- 数据库: `catalog.suites` 表新增 `version VARCHAR(32)` 列
