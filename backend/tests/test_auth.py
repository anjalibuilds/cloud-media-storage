from uuid import uuid4

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_access_token_creation_and_decode():
    user_id = str(uuid4())

    token = create_access_token(user_id)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_refresh_token_creation_and_decode():
    user_id = str(uuid4())

    token = create_refresh_token(user_id)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


def test_access_and_refresh_tokens_are_different():
    user_id = str(uuid4())

    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    assert access_token != refresh_token