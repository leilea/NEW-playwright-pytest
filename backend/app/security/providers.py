from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.security.password import verify_password


class LoginError(Exception):
    pass


class LoginProvider(Protocol):
    name: str

    async def authenticate(self, db: AsyncSession, **credentials) -> User: ...


class LocalPasswordProvider:
    name = "local"

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> User:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active or not user.password_hash:
            raise LoginError("invalid credentials")
        if not verify_password(password, user.password_hash):
            raise LoginError("invalid credentials")
        return user
