from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import raise_authentication_error
from app.core.security import decode_access_token
from app.dependencies.database import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise_authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise jwt.InvalidTokenError("Missing token subject")
        user_id = UUID(subject)
    except (jwt.InvalidTokenError, ValueError):
        raise_authentication_error("INVALID_TOKEN", "The login session is invalid or expired.")

    user = session.get(User, user_id)
    if user is None:
        raise_authentication_error("INVALID_TOKEN", "The login session is invalid or expired.")
    if not user.is_active:
        raise_authentication_error("ACCOUNT_INACTIVE", "This account is inactive.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
