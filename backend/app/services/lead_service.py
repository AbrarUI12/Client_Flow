from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import LeadSource, LeadStatus
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate


def _owned_active_leads_query(owner_id: UUID) -> Select[tuple[Lead]]:
    return select(Lead).where(
        Lead.owner_id == owner_id,
        Lead.is_archived.is_(False),
    )


def get_owned_lead(session: Session, owner_id: UUID, lead_id: UUID) -> Lead | None:
    return session.scalar(_owned_active_leads_query(owner_id).where(Lead.id == lead_id))


def create_lead(session: Session, owner_id: UUID, payload: LeadCreate) -> Lead:
    lead = Lead(owner_id=owner_id, **payload.model_dump())
    session.add(lead)
    session.flush()
    session.refresh(lead)
    return lead


def list_owned_leads(
    session: Session,
    owner_id: UUID,
    *,
    page: int,
    page_size: int,
    search: str | None,
    status: LeadStatus | None,
    source: LeadSource | None,
) -> tuple[list[Lead], int]:
    query = _owned_active_leads_query(owner_id)

    if status is not None:
        query = query.where(Lead.status == status)
    if source is not None:
        query = query.where(Lead.source == source)
    if search:
        escaped = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        query = query.where(
            or_(
                Lead.contact_name.ilike(pattern, escape="\\"),
                Lead.company.ilike(pattern, escape="\\"),
                Lead.email.ilike(pattern, escape="\\"),
                Lead.phone.ilike(pattern, escape="\\"),
            )
        )

    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(
        session.scalars(
            query.order_by(Lead.created_at.desc(), Lead.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return items, total


def update_lead(lead: Lead, payload: LeadUpdate, session: Session) -> Lead:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    session.flush()
    session.refresh(lead)
    return lead


def archive_lead(lead: Lead, session: Session) -> Lead:
    lead.is_archived = True
    session.flush()
    session.refresh(lead)
    return lead
