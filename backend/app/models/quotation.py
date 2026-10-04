from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Sequence,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import QuotationStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.lead import Lead

quotation_number_sequence = Sequence(
    "quotation_number_seq",
    start=1,
    metadata=Base.metadata,
)


class Quotation(TimestampMixin, Base):
    __tablename__ = "quotations"
    __table_args__ = (
        UniqueConstraint("quote_number", name="uq_quotations_quote_number"),
        CheckConstraint(
            "status IN ('DRAFT', 'SENT', 'ACCEPTED', 'REJECTED')",
            name="ck_quotations_status_values",
        ),
        CheckConstraint("valid_until >= issue_date", name="ck_quotations_valid_date_range"),
        CheckConstraint("subtotal >= 0", name="ck_quotations_subtotal_nonnegative"),
        CheckConstraint(
            "discount_percent >= 0 AND discount_percent <= 100",
            name="ck_quotations_discount_percent_range",
        ),
        CheckConstraint(
            "discount_amount >= 0",
            name="ck_quotations_discount_amount_nonnegative",
        ),
        CheckConstraint(
            "tax_percent >= 0 AND tax_percent <= 100",
            name="ck_quotations_tax_percent_range",
        ),
        CheckConstraint("tax_amount >= 0", name="ck_quotations_tax_amount_nonnegative"),
        CheckConstraint("total >= 0", name="ck_quotations_total_nonnegative"),
        Index("ix_quotations_lead_id", "lead_id"),
        Index("ix_quotations_status", "status"),
        Index("ix_quotations_created_at", "created_at"),
        Index("ix_quotations_lead_status", "lead_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    lead_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("leads.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quote_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[QuotationStatus] = mapped_column(
        Enum(
            QuotationStatus,
            name="quotation_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
        ),
        nullable=False,
        default=QuotationStatus.DRAFT,
        server_default=text("'DRAFT'"),
    )
    issue_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        server_default=text("CURRENT_DATE"),
    )
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    tax_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lead: Mapped[Lead] = relationship(back_populates="quotations")
    items: Mapped[list[QuotationItem]] = relationship(
        back_populates="quotation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="QuotationItem.sort_order",
    )


class QuotationItem(Base):
    __tablename__ = "quotation_items"
    __table_args__ = (
        UniqueConstraint(
            "quotation_id",
            "sort_order",
            name="uq_quotation_items_quotation_sort_order",
        ),
        CheckConstraint("quantity > 0", name="ck_quotation_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_quotation_items_unit_price_nonnegative"),
        CheckConstraint("line_total >= 0", name="ck_quotation_items_line_total_nonnegative"),
        CheckConstraint("sort_order >= 0", name="ck_quotation_items_sort_order_nonnegative"),
        Index("ix_quotation_items_quotation_id", "quotation_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    quotation_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped[Quotation] = relationship(back_populates="items")
