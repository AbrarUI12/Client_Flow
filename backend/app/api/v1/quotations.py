from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.errors import raise_not_found
from app.dependencies.auth import CurrentUser
from app.dependencies.database import get_db
from app.models.enums import QuotationStatus
from app.models.lead import Lead
from app.models.quotation import Quotation
from app.schemas.quotation import (
    QuotationCreate,
    QuotationListResponse,
    QuotationResponse,
    QuotationStatusUpdate,
    QuotationUpdate,
)
from app.services.export_service import build_quotation_pdf
from app.services.lead_service import get_owned_lead
from app.services.quotation_service import (
    create_quotation,
    list_owned_quotations,
    require_owned_quotation,
    transition_quotation_status,
    update_draft_quotation,
)

router = APIRouter(tags=["quotations"])


def require_active_owned_lead(session: Session, owner_id: UUID, lead_id: UUID) -> Lead:
    lead = get_owned_lead(session, owner_id, lead_id)
    if lead is None:
        raise_not_found("lead")
    return lead


def quotation_page(
    items: list[Quotation], total: int, page: int, page_size: int
) -> QuotationListResponse:
    return QuotationListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=(total + page_size - 1) // page_size,
    )


@router.post(
    "/leads/{lead_id}/quotations",
    response_model=QuotationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quotation_endpoint(
    lead_id: UUID,
    payload: QuotationCreate,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> Quotation:
    lead = require_active_owned_lead(session, current_user.id, lead_id)
    return create_quotation(session, lead, payload)


@router.get("/leads/{lead_id}/quotations", response_model=QuotationListResponse)
def list_lead_quotations_endpoint(
    lead_id: UUID,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    quotation_status: Annotated[QuotationStatus | None, Query(alias="status")] = None,
) -> QuotationListResponse:
    require_active_owned_lead(session, current_user.id, lead_id)
    items, total = list_owned_quotations(
        session,
        current_user.id,
        page=page,
        page_size=page_size,
        search=None,
        quotation_status=quotation_status,
        lead_id=lead_id,
    )
    return quotation_page(items, total, page, page_size)


@router.get("/quotations", response_model=QuotationListResponse)
def list_quotations_endpoint(
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=100)] = None,
    quotation_status: Annotated[QuotationStatus | None, Query(alias="status")] = None,
) -> QuotationListResponse:
    items, total = list_owned_quotations(
        session,
        current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        quotation_status=quotation_status,
    )
    return quotation_page(items, total, page, page_size)


@router.get("/quotations/{quotation_id}", response_model=QuotationResponse)
def get_quotation_endpoint(
    quotation_id: UUID,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> Quotation:
    return require_owned_quotation(session, current_user.id, quotation_id)


@router.get("/quotations/{quotation_id}/pdf")
def download_quotation_pdf_endpoint(
    quotation_id: UUID,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    quotation = require_owned_quotation(session, current_user.id, quotation_id)
    filename = f"quotation-{quotation.quote_number}.pdf"
    return Response(
        content=build_quotation_pdf(quotation, current_user),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.patch("/quotations/{quotation_id}", response_model=QuotationResponse)
def update_quotation_endpoint(
    quotation_id: UUID,
    payload: QuotationUpdate,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> Quotation:
    quotation = require_owned_quotation(session, current_user.id, quotation_id)
    return update_draft_quotation(session, quotation, payload)


@router.patch("/quotations/{quotation_id}/status", response_model=QuotationResponse)
def update_quotation_status_endpoint(
    quotation_id: UUID,
    payload: QuotationStatusUpdate,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> Quotation:
    quotation = require_owned_quotation(session, current_user.id, quotation_id)
    return transition_quotation_status(session, quotation, payload.status)
