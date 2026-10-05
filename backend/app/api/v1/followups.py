from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy.orm import Session

from app.core.errors import raise_not_found
from app.dependencies.auth import CurrentUser
from app.dependencies.database import DbSession
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.schemas.followup import (
    FollowUpCreate,
    FollowUpListResponse,
    FollowUpResponse,
    FollowUpUpdate,
)
from app.services.followup_service import (
    FollowUpGroup,
    complete_followup,
    create_followup,
    list_owned_followups,
    require_owned_followup,
    update_followup,
)
from app.services.lead_service import get_owned_lead

router = APIRouter(tags=["follow-ups"])


def require_active_owned_lead(session: Session, owner_id: UUID, lead_id: UUID) -> Lead:
    lead = get_owned_lead(session, owner_id, lead_id)
    if lead is None:
        raise_not_found("lead")
    return lead


@router.post(
    "/leads/{lead_id}/follow-ups",
    response_model=FollowUpResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_followup_endpoint(
    lead_id: UUID,
    payload: FollowUpCreate,
    current_user: CurrentUser,
    session: DbSession,
) -> FollowUp:
    lead = require_active_owned_lead(session, current_user.id, lead_id)
    return create_followup(session, lead, payload)


@router.get("/follow-ups", response_model=FollowUpListResponse)
def list_followups_endpoint(
    current_user: CurrentUser,
    session: DbSession,
    group: FollowUpGroup | None = None,
    lead_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> FollowUpListResponse:
    if lead_id is not None:
        require_active_owned_lead(session, current_user.id, lead_id)
    items, total = list_owned_followups(
        session,
        current_user.id,
        timezone_name=current_user.timezone,
        group=group,
        lead_id=lead_id,
    )
    return FollowUpListResponse(items=items[:limit], total=total)


@router.patch("/follow-ups/{followup_id}", response_model=FollowUpResponse)
def update_followup_endpoint(
    followup_id: UUID,
    payload: FollowUpUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> FollowUp:
    followup = require_owned_followup(session, current_user.id, followup_id, for_update=True)
    return update_followup(session, followup, payload)


@router.patch("/follow-ups/{followup_id}/complete", response_model=FollowUpResponse)
def complete_followup_endpoint(
    followup_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> FollowUp:
    followup = require_owned_followup(session, current_user.id, followup_id, for_update=True)
    return complete_followup(session, followup)
