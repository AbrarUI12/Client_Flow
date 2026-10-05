from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import LeadStatus, QuotationStatus
from app.models.lead import Lead
from app.models.quotation import Quotation, QuotationItem, quotation_number_sequence
from app.schemas.quotation import QuotationCreate, QuotationItemInput, QuotationUpdate

MONEY_QUANTUM = Decimal("0.01")
PERCENT_DIVISOR = Decimal("100")
MAX_MONEY = Decimal("999999999999.99")


@dataclass(frozen=True)
class CalculatedItem:
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    sort_order: int


@dataclass(frozen=True)
class QuotationTotals:
    items: list[CalculatedItem]
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal


def round_money(value: Decimal) -> Decimal:
    """Round every persisted monetary result to cents using ROUND_HALF_UP."""
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def calculate_quotation(
    items: list[QuotationItemInput],
    discount_percent: Decimal,
    tax_percent: Decimal,
) -> QuotationTotals:
    calculated_items = [
        CalculatedItem(
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=round_money(item.quantity * item.unit_price),
            sort_order=index,
        )
        for index, item in enumerate(items)
    ]
    subtotal = round_money(sum((item.line_total for item in calculated_items), Decimal("0")))
    discount_amount = round_money(subtotal * discount_percent / PERCENT_DIVISOR)
    discounted_subtotal = subtotal - discount_amount
    tax_amount = round_money(discounted_subtotal * tax_percent / PERCENT_DIVISOR)
    total = round_money(discounted_subtotal + tax_amount)

    if any(value > MAX_MONEY for value in (subtotal, discount_amount, tax_amount, total)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "QUOTATION_TOTAL_TOO_LARGE",
                "message": "The calculated quotation amount exceeds the supported limit.",
            },
        )

    return QuotationTotals(
        items=calculated_items,
        subtotal=subtotal,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        total=total,
    )


def _quotation_load_options() -> tuple[object, ...]:
    return (selectinload(Quotation.items), selectinload(Quotation.lead))


def _owned_quotations_query(owner_id: UUID) -> Select[tuple[Quotation]]:
    # Quotations follow their lead's archive state, matching the dashboard and lead routes.
    return (
        select(Quotation)
        .join(Quotation.lead)
        .where(Lead.owner_id == owner_id, Lead.is_archived.is_(False))
        .options(*_quotation_load_options())
    )


def get_owned_quotation(
    session: Session,
    owner_id: UUID,
    quotation_id: UUID,
    *,
    for_update: bool = False,
) -> Quotation | None:
    query = _owned_quotations_query(owner_id).where(Quotation.id == quotation_id)
    if for_update:
        # Lock the row so concurrent edits or transitions re-check the committed status.
        query = query.with_for_update(of=Quotation).execution_options(populate_existing=True)
    return session.scalar(query)


def _next_quote_number(session: Session, issue_date: date) -> str:
    # The PostgreSQL sequence is concurrency-safe; gaps after rollbacks are acceptable.
    sequence_value = session.scalar(select(quotation_number_sequence.next_value()))
    assert sequence_value is not None
    return f"Q-{issue_date.year}-{sequence_value:06d}"


def _build_items(totals: QuotationTotals) -> list[QuotationItem]:
    return [
        QuotationItem(
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.line_total,
            sort_order=item.sort_order,
        )
        for item in totals.items
    ]


def create_quotation(session: Session, lead: Lead, payload: QuotationCreate) -> Quotation:
    totals = calculate_quotation(payload.items, payload.discount_percent, payload.tax_percent)
    quotation = Quotation(
        lead=lead,
        quote_number=_next_quote_number(session, payload.issue_date),
        issue_date=payload.issue_date,
        valid_until=payload.valid_until,
        subtotal=totals.subtotal,
        discount_percent=payload.discount_percent,
        discount_amount=totals.discount_amount,
        tax_percent=payload.tax_percent,
        tax_amount=totals.tax_amount,
        total=totals.total,
        notes=payload.notes,
        items=_build_items(totals),
    )
    session.add(quotation)
    session.flush()
    return require_owned_quotation(session, lead.owner_id, quotation.id)


def list_owned_quotations(
    session: Session,
    owner_id: UUID,
    *,
    page: int,
    page_size: int,
    search: str | None,
    quotation_status: QuotationStatus | None,
    lead_id: UUID | None = None,
) -> tuple[list[Quotation], int]:
    query = _owned_quotations_query(owner_id)
    if lead_id is not None:
        query = query.where(Quotation.lead_id == lead_id)
    if quotation_status is not None:
        query = query.where(Quotation.status == quotation_status)
    if search:
        escaped = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        query = query.where(
            or_(
                Quotation.quote_number.ilike(pattern, escape="\\"),
                Lead.contact_name.ilike(pattern, escape="\\"),
                Lead.company.ilike(pattern, escape="\\"),
                Lead.email.ilike(pattern, escape="\\"),
            )
        )

    count_query = select(func.count()).select_from(query.order_by(None).options().subquery())
    total = session.scalar(count_query) or 0
    quotations = list(
        session.scalars(
            query.order_by(Quotation.created_at.desc(), Quotation.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return quotations, total


def update_draft_quotation(
    session: Session,
    quotation: Quotation,
    payload: QuotationUpdate,
) -> Quotation:
    if quotation.status != QuotationStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "QUOTATION_NOT_EDITABLE",
                "message": "Only draft quotations can be edited.",
            },
        )

    issue_date = payload.issue_date if payload.issue_date is not None else quotation.issue_date
    valid_until = payload.valid_until if payload.valid_until is not None else quotation.valid_until
    if valid_until < issue_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "INVALID_QUOTATION_DATE_RANGE",
                "message": "The valid-until date must be on or after the issue date.",
            },
        )

    items_input = payload.items
    if items_input is None:
        items_input = [
            QuotationItemInput(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in quotation.items
        ]
    discount_percent = (
        payload.discount_percent
        if payload.discount_percent is not None
        else quotation.discount_percent
    )
    tax_percent = payload.tax_percent if payload.tax_percent is not None else quotation.tax_percent
    totals = calculate_quotation(items_input, discount_percent, tax_percent)

    quotation.issue_date = issue_date
    quotation.valid_until = valid_until
    quotation.discount_percent = discount_percent
    quotation.tax_percent = tax_percent
    quotation.subtotal = totals.subtotal
    quotation.discount_amount = totals.discount_amount
    quotation.tax_amount = totals.tax_amount
    quotation.total = totals.total
    if "notes" in payload.model_fields_set:
        quotation.notes = payload.notes

    if payload.items is not None:
        quotation.items.clear()
        session.flush()
        quotation.items = _build_items(totals)

    session.flush()
    return require_owned_quotation(session, quotation.lead.owner_id, quotation.id)


LEGAL_STATUS_TRANSITIONS: dict[QuotationStatus, set[QuotationStatus]] = {
    QuotationStatus.DRAFT: {QuotationStatus.SENT},
    QuotationStatus.SENT: {QuotationStatus.ACCEPTED, QuotationStatus.REJECTED},
    QuotationStatus.ACCEPTED: set(),
    QuotationStatus.REJECTED: set(),
}


def transition_quotation_status(
    session: Session,
    quotation: Quotation,
    new_status: QuotationStatus,
) -> Quotation:
    if new_status not in LEGAL_STATUS_TRANSITIONS[quotation.status]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INVALID_QUOTATION_STATUS_TRANSITION",
                "message": (
                    f"A quotation cannot move from {quotation.status} to {new_status}."
                ),
            },
        )

    now = datetime.now(UTC)
    quotation.status = new_status
    if new_status == QuotationStatus.SENT:
        quotation.sent_at = now
        if quotation.lead.status not in {LeadStatus.WON, LeadStatus.LOST}:
            quotation.lead.status = LeadStatus.QUOTED
    elif new_status == QuotationStatus.ACCEPTED:
        quotation.accepted_at = now
        quotation.lead.status = LeadStatus.WON
    elif new_status == QuotationStatus.REJECTED:
        quotation.rejected_at = now

    session.flush()
    return require_owned_quotation(session, quotation.lead.owner_id, quotation.id)


def require_owned_quotation(
    session: Session,
    owner_id: UUID,
    quotation_id: UUID,
    *,
    for_update: bool = False,
) -> Quotation:
    quotation = get_owned_quotation(session, owner_id, quotation_id, for_update=for_update)
    if quotation is None:
        from app.core.errors import raise_not_found

        raise_not_found("quotation")
    return quotation
