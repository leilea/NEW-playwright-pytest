import pytest

from app.models.auth import User
from app.security.password import hash_password
from app.security.providers import LocalPasswordProvider, LoginError


@pytest.mark.asyncio
async def test_local_provider_authenticates(db_session):
    user = User(email="t@e.st", display_name="T", password_hash=hash_password("pw"))
    db_session.add(user)
    await db_session.flush()
    p = LocalPasswordProvider()
    u = await p.authenticate(db_session, email="t@e.st", password="pw")
    assert u.id == user.id


@pytest.mark.asyncio
async def test_local_provider_rejects_wrong_password(db_session):
    user = User(email="t@e.st", password_hash=hash_password("right"))
    db_session.add(user)
    await db_session.flush()
    p = LocalPasswordProvider()
    with pytest.raises(LoginError):
        await p.authenticate(db_session, email="t@e.st", password="wrong")
