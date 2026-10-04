import os
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import LeadStatus, QuotationStatus
from app.models.lead import Lead
from app.models.quotation import (
    Quotation,
    QuotationItem,
    quotation_number_sequence,
)
from app.models.user import User
from app.schemas.quotation import QuotationCreate, QuotationItemInput, QuotationUpdate
from app.services.quotation_service import (
    create_quotation,
    transition_quotation_status,
    update_draft_quotation,
)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="TEST_DATABASE_URL is required for PostgreSQL integration tests",
)
def test_postgresql_constraints_sequence_and_item_cascade() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL)

    with Session(engine) as session:
        owner = session.scalar(select(User).where(User.email == "demo@clientflow.app"))
        assert owner is not None

        sequence_value = session.scalar(select(quotation_number_sequence.next_value()))
        assert sequence_value is not None

        lead = Lead(
            owner_id=owner.id,
            contact_name="Session 2 Verification",
            estimated_value=Decimal("100.00"),
        )
        session.add(lead)
        session.flush()

        quotation = Quotation(
            lead_id=lead.id,
            quote_number=f"Q-{date.today().year}-{sequence_value:05d}",
            valid_until=date.today() + timedelta(days=14),
        )
        session.add(quotation)
        session.flush()

        item = QuotationItem(
            quotation_id=quotation.id,
            description="Database verification item",
            quantity=Decimal("1.000"),
            unit_price=Decimal("100.00"),
            line_total=Decimal("100.00"),
            sort_order=0,
        )
        session.add(item)
        session.commit()

        item_id = item.id
        lead_id = lead.id
        session.execute(delete(Quotation).where(Quotation.id == quotation.id))
        session.commit()
        assert session.get(QuotationItem, item_id) is None

        session.execute(delete(Lead).where(Lead.id == lead_id))
        session.commit()

        invalid_lead = Lead(
            owner_id=owner.id,
            contact_name="Invalid negative value",
            estimated_value=Decimal("-0.01"),
        )
        session.add(invalid_lead)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


@pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="TEST_DATABASE_URL is required for PostgreSQL integration tests",
)
def test_postgresql_quotation_engine_and_transitions() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL)

    with Session(engine, expire_on_commit=False) as session:
        try:
            owner = session.scalar(select(User).where(User.email == "demo@clientflow.app"))
            assert owner is not None
            lead = Lead(
                owner_id=owner.id,
                contact_name=f"PostgreSQL quote test {uuid4()}",
                status=LeadStatus.QUALIFIED,
                estimated_value=Decimal("100.00"),
            )
            session.add(lead)
            session.flush()

            quote = create_quotation(
                session,
                lead,
                QuotationCreate(
                    issue_date=date.today(),
                    valid_until=date.today() + timedelta(days=14),
                    discount_percent=Decimal("10.00"),
                    tax_percent=Decimal("5.00"),
                    items=[
                        QuotationItemInput(
                            description="PostgreSQL service",
                            quantity=Decimal("2.500"),
                            unit_price=Decimal("20.00"),
                        )
                    ],
                ),
            )
            assert quote.quote_number.startswith(f"Q-{date.today().year}-")
            assert quote.subtotal == Decimal("50.00")
            assert quote.discount_amount == Decimal("5.00")
            assert quote.tax_amount == Decimal("2.25")
            assert quote.total == Decimal("47.25")

            edited = update_draft_quotation(
                session,
                quote,
                QuotationUpdate(
                    items=[
                        QuotationItemInput(
                            description="Replacement scope",
                            quantity=Decimal("3.000"),
                            unit_price=Decimal("25.00"),
                        )
                    ]
                ),
            )
            assert len(edited.items) == 1
            assert edited.total == Decimal("70.88")

            sent = transition_quotation_status(session, edited, QuotationStatus.SENT)
            assert sent.status == QuotationStatus.SENT
            accepted = transition_quotation_status(session, sent, QuotationStatus.ACCEPTED)
            assert accepted.status == QuotationStatus.ACCEPTED
            assert accepted.lead.status == LeadStatus.WON
        finally:
            session.rollback()

    engine.dispose()
