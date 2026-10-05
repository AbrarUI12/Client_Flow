from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import LeadStatus, QuotationStatus
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.quotation import Quotation
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.followup_service import local_day_bounds

OPEN_QUOTATION_STATUSES = (QuotationStatus.DRAFT, QuotationStatus.SENT)
DASHBOARD_ROW_LIMIT = 5


def build_dashboard_summary(
    session: Session,
    user: User,
    *,
    now: datetime | None = None,
) -> DashboardSummaryResponse:
    active_lead_filter = (
        Lead.owner_id == user.id,
        Lead.is_archived.is_(False),
    )
    total_leads = session.scalar(
        select(func.count()).select_from(Lead).where(*active_lead_filter)
    ) or 0

    pipeline_rows = session.execute(
        select(Lead.status, func.count())
        .where(*active_lead_filter)
        .group_by(Lead.status)
    ).all()
    pipeline_counts = {lead_status: 0 for lead_status in LeadStatus}
    pipeline_counts.update({lead_status: count for lead_status, count in pipeline_rows})

    quote_count, quote_value = session.execute(
        select(
            func.count(Quotation.id),
            func.coalesce(func.sum(Quotation.total), Decimal("0.00")),
        )
        .join(Quotation.lead)
        .where(
            *active_lead_filter,
            Quotation.status.in_(OPEN_QUOTATION_STATUSES),
        )
    ).one()

    start_of_today, _ = local_day_bounds(user.timezone, now or datetime.now(UTC))
    active_followups = (
        select(FollowUp)
        .join(FollowUp.lead)
        .where(*active_lead_filter, FollowUp.is_completed.is_(False))
        .options(selectinload(FollowUp.lead))
    )
    overdue_filter = FollowUp.due_at < start_of_today
    overdue_followup_count = session.scalar(
        select(func.count()).select_from(active_followups.where(overdue_filter).subquery())
    ) or 0
    overdue_followups = list(
        session.scalars(
            active_followups.where(overdue_filter)
            .order_by(FollowUp.due_at.asc(), FollowUp.id.asc())
            .limit(DASHBOARD_ROW_LIMIT)
        )
    )
    upcoming_followups = list(
        session.scalars(
            active_followups.where(FollowUp.due_at >= start_of_today)
            .order_by(FollowUp.due_at.asc(), FollowUp.id.asc())
            .limit(DASHBOARD_ROW_LIMIT)
        )
    )
    recent_leads = list(
        session.scalars(
            select(Lead)
            .where(*active_lead_filter)
            .order_by(Lead.created_at.desc(), Lead.id.desc())
            .limit(DASHBOARD_ROW_LIMIT)
        )
    )

    return DashboardSummaryResponse(
        total_leads=total_leads,
        open_quotation_count=quote_count,
        open_quotation_value=quote_value,
        overdue_followup_count=overdue_followup_count,
        pipeline_counts=pipeline_counts,
        overdue_followups=overdue_followups,
        upcoming_followups=upcoming_followups,
        recent_leads=recent_leads,
    )
