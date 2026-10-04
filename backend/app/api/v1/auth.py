from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import raise_authentication_error
from app.core.security import create_access_token, verify_password_or_dummy
from app.dependencies.auth import CurrentUser
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.auth import CurrentUserResponse, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    email = str(credentials.email).strip().lower()
    user = session.scalar(select(User).where(User.email == email))
    password_is_valid = verify_password_or_dummy(
        credentials.password,
        user.password_hash if user is not None else None,
    )

    if user is None or not password_is_valid or not user.is_active:
        raise_authentication_error(
            "INVALID_CREDENTIALS",
            "The email or password is incorrect.",
        )

    access_token, expires_in = create_access_token(user.id)
    return TokenResponse(access_token=access_token, expires_in=expires_in)


@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: CurrentUser) -> User:
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_: CurrentUser) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)
