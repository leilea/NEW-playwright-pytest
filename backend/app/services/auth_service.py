from app.config import settings
from app.security.providers import LocalPasswordProvider, LoginError
from app.security.jwt import issue_token


class LoginFailed(Exception):
    pass


async def login_with_password(db, *, email: str, password: str):
    provider = LocalPasswordProvider()
    try:
        user = await provider.authenticate(db, email=email, password=password)
    except LoginError as e:
        raise LoginFailed(str(e)) from e
    token = issue_token(settings, user_id=user.id, email=user.email)
    return token, user
