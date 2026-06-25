## 上下文

`backend/alembic/versions/0002_add_suite_version.py` 迁移已创建，但从未应用到数据库。当前 `catalog.suites` 表有 6 列（id, legacy_id, name, description, owner_id, created_at, updated_at），ORM 模型需要第 8 列 `version`。

## 目标 / 非目标

**目标：**
- 应用迁移 `0002`，向 `catalog.suites` 添加 `version` 列

**非目标：**
- 不修改任何代码
- 不涉及数据迁移

## 决策

- 使用 `alembic upgrade head` 一次执行所有待处理迁移，幂等安全
- 迁移操作仅为 `ADD COLUMN version VARCHAR(32) DEFAULT ''`

## 风险 / 权衡

- 若数据库中已有 `alembic_version` 记录为 `0001`，则仅执行 `0002`；若表被手动创建无记录，则从头执行全部迁移
