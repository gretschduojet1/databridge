import pytest
from jose import JWTError

from core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_create_and_decode_access_token() -> None:
    token = create_access_token(subject="user@example.com", role="admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "user@example.com"
    assert payload["role"] == "admin"


def test_decode_invalid_token_raises() -> None:
    with pytest.raises(JWTError):
        decode_access_token("not.a.valid.token")
