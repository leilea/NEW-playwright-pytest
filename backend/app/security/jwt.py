from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt


def issue_token(settings, *, user_id: int, email: str, ttl_min: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    ttl = ttl_min if ttl_min is not None else settings.jwt_ttl_min
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_token(settings, token: str, ttl_min: int | None = None) -> dict:
    try:
        options = {}
        if ttl_min is not None:
            options = {"verify_exp": ttl_min >= 0}
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg], options=options)
    except JWTError as e:
        raise ValueError(f"invalid token: {e}") from e
