from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import LeadSource, LeadStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.followup import FollowUp
    from app.models.quotation import Quotation
    from app.models.user import User


class Lead(TimestampMixin, Base):
    __tablename__ = "leads"
    __table_args__ = (
        CheckConstraint("estimated_value >= 0", name="ck_leads_estimated_value_nonnegative"),
        CheckConstraint(
            "status IN ('NEW', 'CONTACTED', 'QUALIFIED', 'QUOTED', 'WON', 'LOST')",
            name="ck_leads_status_values",
        ),
        CheckConstraint(
            "source IS NULL OR source IN "
            "('WEBSITE', 'REFERRAL', 'LINKEDIN', 'UPWORK', 'FIVERR', 'EMAIL', 'PHONE', 'OTHER')",
            name="ck_leads_source_values",
        ),
        Index("ix_leads_owner_id", "owner_id"),
        Index("ix_leads_status", "status"),
        Index("ix_leads_created_at", "created_at"),
        Index("ix_leads_is_archived", "is_archived"),
        Index("ix_leads_owner_active_created", "owner_id", "is_archived", "created_at"),
        Index("ix_leads_owner_status", "owner_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[str | None] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[LeadSource | None] = mapped_column(
        Enum(
            LeadSource,
            name="lead_source",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
        )
    )
    status: Mapped[LeadStatus] = mapped_column(
        Enum(
            LeadStatus,
            name="lead_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
        ),
        nullable=False,
        default=LeadStatus.NEW,
        server_default=text("'NEW'"),
    )
    estimated_value: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )

    owner: Mapped[User] = relationship(back_populates="leads")
    quotations: Mapped[list[Quotation]] = relationship(back_populates="lead")
    follow_ups: Mapped[list[FollowUp]] = relationship(back_populates="lead")
