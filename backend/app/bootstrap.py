from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import SessionLocal
from app.models.auth import User, Role, UserRole
from app.security.password import hash_password


async def bootstrap_admin() -> None:
    async with SessionLocal() as session:
        users_count = await session.scalar(select(func.count()).select_from(User))
        if users_count and users_count > 0:
            return

        role_select = await session.execute(
            select(Role).where(Role.name == "admin")
        )
        admin_role = role_select.scalar_one_or_none()
        if admin_role is None:
            admin_role = Role(name="admin")
            session.add(admin_role)
            await session.flush()

        if not (await session.scalar(select(Role).where(Role.name == "editor"))):
            session.add(Role(name="editor"))
        if not (await session.scalar(select(Role).where(Role.name == "viewer"))):
            session.add(Role(name="viewer"))
        await session.flush()

        user = User(
            email=settings.bootstrap_admin_email,
            display_name="Bootstrap Admin",
            password_hash=hash_password(settings.bootstrap_admin_password),
            provider="local",
        )
        session.add(user)
        await session.flush()

        session.add(UserRole(user_id=user.id, role_id=admin_role.id))
        await session.commit()
