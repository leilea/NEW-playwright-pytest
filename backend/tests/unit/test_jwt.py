import time

import pytest
from app.config import Settings
from app.security.jwt import decode_token, issue_token


def test_issue_decode_roundtrip():
    s = Settings(jwt_secret="x" * 32, jwt_ttl_min=5)
    tok = issue_token(s, user_id=42, email="a@b.c")
    payload = decode_token(s, tok)
    assert payload["sub"] == "42"
    assert payload["email"] == "a@b.c"


def test_expired_token_rejected():
    s = Settings(jwt_secret="x" * 32, jwt_ttl_min=5)
    tok = issue_token(s, user_id=1, email="a@b.c", ttl_min=-1)
    with pytest.raises(ValueError, match="invalid token"):
        decode_token(s, tok)
