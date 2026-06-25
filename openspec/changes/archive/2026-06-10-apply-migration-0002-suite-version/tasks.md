## 1. 执行数据库迁移

- [x] 1.1 检查当前 alembic 迁移状态
- [x] 1.2 执行 `alembic upgrade head` 应用遗漏迁移
- [x] 1.3 验证 `catalog.suites` 表已包含 `version` 列
- [x] 1.4 确认 API `/api/suites` 可正常返回数据
