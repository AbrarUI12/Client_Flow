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


def raise_not_found(resource: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": f"{resource.upper()}_NOT_FOUND",
            "message": f"The requested {resource.lower()} was not found.",
        },
    )
