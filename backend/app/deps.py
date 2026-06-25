from typing import AsyncIterator

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.security.jwt import decode_token
from app.config import settings
from app.models.auth import User, UserRole


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(request: Request, db=Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    auth = request.headers.get("authorization", "")
    if not token and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
    if not token:
        raise HTTPException(401, "missing token")
    try:
        payload = decode_token(settings, token)
    except ValueError:
        raise HTTPException(401, "invalid token")
    uid = int(payload["sub"])
    res = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.id == uid)
    )
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "user not found or inactive")
    return user
