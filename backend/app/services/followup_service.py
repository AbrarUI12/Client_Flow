from datetime import UTC, datetime, time, timedelta
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import raise_not_found
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.schemas.followup import FollowUpCreate, FollowUpUpdate


class FollowUpGroup(StrEnum):
    OVERDUE = "overdue"
    TODAY = "today"
    UPCOMING = "upcoming"
    COMPLETED = "completed"


def _owned_followups_query(owner_id: UUID) -> Select[tuple[FollowUp]]:
    # Follow-ups follow their lead's archive state, matching the dashboard and lead routes.
    return (
        select(FollowUp)
        .join(FollowUp.lead)
        .where(Lead.owner_id == owner_id, Lead.is_archived.is_(False))
        .options(selectinload(FollowUp.lead))
    )


def get_owned_followup(
    session: Session,
    owner_id: UUID,
    followup_id: UUID,
    *,
    for_update: bool = False,
) -> FollowUp | None:
    query = _owned_followups_query(owner_id).where(FollowUp.id == followup_id)
    if for_update:
        # Lock the row so a concurrent edit and completion re-check the committed state.
        query = query.with_for_update(of=FollowUp).execution_options(populate_existing=True)
    return session.scalar(query)


def require_owned_followup(
    session: Session,
    owner_id: UUID,
    followup_id: UUID,
    *,
    for_update: bool = False,
) -> FollowUp:
    followup = get_owned_followup(session, owner_id, followup_id, for_update=for_update)
    if followup is None:
        raise_not_found("follow-up")
    return followup


def create_followup(session: Session, lead: Lead, payload: FollowUpCreate) -> FollowUp:
    followup = FollowUp(lead=lead, due_at=payload.due_at, note=payload.note)
    session.add(followup)
    session.flush()
    return require_owned_followup(session, lead.owner_id, followup.id)


def local_day_bounds(timezone_name: str, now: datetime) -> tuple[datetime, datetime]:
    timezone = ZoneInfo(timezone_name)
    local_date = now.astimezone(timezone).date()
    start = datetime.combine(local_date, time.min, tzinfo=timezone).astimezone(UTC)
    end = (datetime.combine(local_date, time.min, tzinfo=timezone) + timedelta(days=1)).astimezone(
        UTC
    )
    return start, end


def list_owned_followups(
    session: Session,
    owner_id: UUID,
    *,
    timezone_name: str,
    group: FollowUpGroup | None,
    lead_id: UUID | None = None,
    now: datetime | None = None,
) -> tuple[list[FollowUp], int]:
    query = _owned_followups_query(owner_id)
    if lead_id is not None:
        query = query.where(FollowUp.lead_id == lead_id)

    start, end = local_day_bounds(timezone_name, now or datetime.now(UTC))
    if group == FollowUpGroup.COMPLETED:
        query = query.where(FollowUp.is_completed.is_(True)).order_by(
            FollowUp.completed_at.desc(), FollowUp.id.desc()
        )
    elif group == FollowUpGroup.OVERDUE:
        query = query.where(
            FollowUp.is_completed.is_(False), FollowUp.due_at < start
        ).order_by(FollowUp.due_at.asc(), FollowUp.id.asc())
    elif group == FollowUpGroup.TODAY:
        query = query.where(
            FollowUp.is_completed.is_(False),
            FollowUp.due_at >= start,
            FollowUp.due_at < end,
        ).order_by(FollowUp.due_at.asc(), FollowUp.id.asc())
    elif group == FollowUpGroup.UPCOMING:
        query = query.where(
            FollowUp.is_completed.is_(False), FollowUp.due_at >= end
        ).order_by(FollowUp.due_at.asc(), FollowUp.id.asc())
    else:
        query = query.order_by(
            FollowUp.is_completed.asc(), FollowUp.due_at.asc(), FollowUp.id.asc()
        )

    count_query = select(func.count()).select_from(query.order_by(None).options().subquery())
    total = session.scalar(count_query) or 0
    return list(session.scalars(query)), total


def update_followup(session: Session, followup: FollowUp, payload: FollowUpUpdate) -> FollowUp:
    if followup.is_completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "FOLLOW_UP_NOT_EDITABLE",
                "message": "Completed follow-ups cannot be edited.",
            },
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(followup, field, value)
    session.flush()
    return require_owned_followup(session, followup.lead.owner_id, followup.id)


def complete_followup(session: Session, followup: FollowUp) -> FollowUp:
    # Completion is intentionally idempotent so retries preserve the original completion time.
    if not followup.is_completed:
        followup.is_completed = True
        followup.completed_at = datetime.now(UTC)
        session.flush()
    return require_owned_followup(session, followup.lead.owner_id, followup.id)
