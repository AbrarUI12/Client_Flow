from typing import NoReturn

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
    code_prefix = resource.upper().replace("-", "_").replace(" ", "_")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": f"{code_prefix}_NOT_FOUND",
            "message": f"The requested {resource.lower()} was not found.",
        },
    )


async def request_validation_error_handler(
    _: Request, error: RequestValidationError
) -> JSONResponse:
    # Unlike FastAPI's default, never echo submitted values: they can contain passwords, and
    # malformed text (such as lone surrogates) cannot be encoded into the response.
    errors = [
        {key: value for key, value in item.items() if key != "input"} for item in error.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": jsonable_encoder(errors)},
    )
