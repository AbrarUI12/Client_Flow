from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import request_validation_error_handler

settings = get_settings()
api_docs_enabled = settings.environment != "production" or settings.expose_api_docs

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if api_docs_enabled else None,
    redoc_url=None,
    openapi_url="/openapi.json" if api_docs_enabled else None,
)

# The SPA authenticates with a bearer header, not cookies, so credentials stay disabled and only
# the methods and headers the frontend actually sends are allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Accept", "Authorization", "Content-Type"],
    expose_headers=["Content-Disposition"],
)

app.add_exception_handler(RequestValidationError, request_validation_error_handler)
app.include_router(api_router, prefix=settings.api_v1_prefix)
