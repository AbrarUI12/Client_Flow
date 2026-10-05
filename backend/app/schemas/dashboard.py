from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import LeadStatus
from app.schemas.followup import FollowUpResponse
from app.schemas.lead import LeadResponse


class DashboardSummaryResponse(BaseModel):
    total_leads: int
    open_quotation_count: int
    open_quotation_value: Decimal
    overdue_followup_count: int
    pipeline_counts: dict[LeadStatus, int]
    overdue_followups: list[FollowUpResponse]
    upcoming_followups: list[FollowUpResponse]
    recent_leads: list[LeadResponse]
