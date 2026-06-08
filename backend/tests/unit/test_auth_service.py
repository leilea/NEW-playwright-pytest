import pytest

from app.services.auth_service import login_with_password, LoginFailed
from app.security.password import hash_password
from app.models.auth import User


@pytest.mark.asyncio
async def test_login_returns_token_and_user(db_session):
    db_session.add(User(email="a@b.c", password_hash=hash_password("x")))
    await db_session.flush()
    token, user = await login_with_password(db_session, email="a@b.c", password="x")
    assert token and user.email == "a@b.c"


@pytest.mark.asyncio
async def test_login_wrong_raises(db_session):
    db_session.add(User(email="a@b.c", password_hash=hash_password("x")))
    await db_session.flush()
    with pytest.raises(LoginFailed):
        await login_with_password(db_session, email="a@b.c", password="y")
