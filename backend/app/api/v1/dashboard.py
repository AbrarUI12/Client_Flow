from fastapi import APIRouter

from app.dependencies.auth import CurrentUser
from app.dependencies.database import DbSession
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import build_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary_endpoint(
    current_user: CurrentUser,
    session: DbSession,
) -> DashboardSummaryResponse:
    return build_dashboard_summary(session, current_user)
