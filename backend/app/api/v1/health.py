from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.dependencies.database import DbSession

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


@router.get("/health", response_model=HealthResponse, summary="Check API health")
def health_check(session: DbSession) -> HealthResponse:
    # Production uses this as a readiness check, so success proves the API and PostgreSQL are ready.
    session.execute(text("SELECT 1"))
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )
