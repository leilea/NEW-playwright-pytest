# app/models/__init__.py - 子包导入触发模型注册 (alembic env.py 用)
from app.models.auth import User, Role, UserRole, ResourceACL  # noqa: F401
