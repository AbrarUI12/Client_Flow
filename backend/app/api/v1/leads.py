from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.params import PageQuery, PageSizeQuery, SearchQuery
from app.core.errors import raise_not_found
from app.dependencies.auth import CurrentUser
from app.dependencies.database import DbSession
from app.models.enums import LeadSource, LeadStatus
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadListResponse, LeadResponse, LeadUpdate
from app.services.export_service import build_leads_csv, leads_export_filename
from app.services.lead_service import (
    archive_lead,
    create_lead,
    get_owned_lead,
    list_owned_leads,
    update_lead,
)

router = APIRouter(prefix="/leads", tags=["leads"])


def require_owned_lead(session: Session, owner_id: UUID, lead_id: UUID) -> Lead:
    lead = get_owned_lead(session, owner_id, lead_id)
    if lead is None:
        raise_not_found("lead")
    return lead


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead_endpoint(
    payload: LeadCreate,
    current_user: CurrentUser,
    session: DbSession,
) -> Lead:
    return create_lead(session, current_user.id, payload)


@router.get("/export")
def export_leads_endpoint(
    current_user: CurrentUser,
    session: DbSession,
) -> Response:
    filename = leads_export_filename()
    return Response(
        content=build_leads_csv(session, current_user),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("", response_model=LeadListResponse)
def list_leads_endpoint(
    current_user: CurrentUser,
    session: DbSession,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 20,
    search: SearchQuery = None,
    lead_status: Annotated[LeadStatus | None, Query(alias="status")] = None,
    source: LeadSource | None = None,
) -> LeadListResponse:
    items, total = list_owned_leads(
        session,
        current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        status=lead_status,
        source=source,
    )
    return LeadListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead_endpoint(
    lead_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> Lead:
    return require_owned_lead(session, current_user.id, lead_id)


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead_endpoint(
    lead_id: UUID,
    payload: LeadUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> Lead:
    lead = require_owned_lead(session, current_user.id, lead_id)
    return update_lead(lead, payload, session)


@router.post("/{lead_id}/archive", response_model=LeadResponse)
def archive_lead_endpoint(
    lead_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> Lead:
    lead = require_owned_lead(session, current_user.id, lead_id)
    return archive_lead(lead, session)
