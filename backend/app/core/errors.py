from typing import NoReturn

from fastapi import HTTPException, status


def raise_authentication_error(
    code: str = "AUTHENTICATION_REQUIRED",
    message: str = "A valid login session is required.",
) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": code, "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )
