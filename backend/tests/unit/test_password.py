from app.security.password import hash_password, verify_password


def test_hash_and_verify_roundtrip():
    h = hash_password("hunter2-correct")
    assert h.startswith("$argon2id$")
    assert verify_password("hunter2-correct", h) is True
    assert verify_password("hunter2-wrong", h) is False
