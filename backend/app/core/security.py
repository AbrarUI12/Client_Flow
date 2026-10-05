from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings

password_hasher = PasswordHasher()
dummy_password_hash = password_hasher.hash("clientflow-dummy-password")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def verify_password_or_dummy(password: str, password_hash: str | None) -> bool:
    return verify_password(password, password_hash or dummy_password_hash)


def create_access_token(
    subject: UUID | str,
    *,
    expires_delta: timedelta | None = None,
) -> tuple[str, int]:
    settings = get_settings()
    lifetime = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    now = datetime.now(UTC)
    expires_at = now + lifetime
    payload = {
        "sub": str(subject),
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    return token, max(0, int(lifetime.total_seconds()))


def decode_access_token(token: str) -> dict[str, object]:
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "sub", "type"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload
