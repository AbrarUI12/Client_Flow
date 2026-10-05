from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import LeadStatus, QuotationStatus
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.quotation import Quotation, QuotationItem
from app.models.user import User
from app.scripts.seed_demo_user import DEMO_LEADS, seed_demo_data
from app.services.followup_service import FollowUpGroup, list_owned_followups

FIXED_NOW = datetime(2026, 10, 5, 6, 0, tzinfo=UTC)


def _owned_counts(session: Session, owner_id: object) -> tuple[int, int, int, int]:
    lead_ids = select(Lead.id).where(Lead.owner_id == owner_id)
    quotation_ids = select(Quotation.id).where(Quotation.lead_id.in_(lead_ids))
    return (
        session.scalar(select(func.count()).select_from(Lead).where(Lead.owner_id == owner_id))
        or 0,
        session.scalar(
            select(func.count()).select_from(Quotation).where(Quotation.lead_id.in_(lead_ids))
        )
        or 0,
        session.scalar(
            select(func.count())
            .select_from(QuotationItem)
            .where(QuotationItem.quotation_id.in_(quotation_ids))
        )
        or 0,
        session.scalar(
            select(func.count()).select_from(FollowUp).where(FollowUp.lead_id.in_(lead_ids))
        )
        or 0,
    )


def test_seed_creates_complete_relative_dataset_and_is_idempotent(db_session: Session) -> None:
    settings = Settings(_env_file=None)

    first = seed_demo_data(db_session, settings, now=FIXED_NOW)
    saved_due_dates = list(db_session.scalars(select(FollowUp.due_at).order_by(FollowUp.id)))
    second = seed_demo_data(db_session, settings, now=FIXED_NOW + timedelta(days=20))

    assert first.dataset_created is True
    assert second.dataset_created is False
    assert first.user.id == second.user.id
    assert _owned_counts(db_session, first.user.id) == (30, 8, 21, 12)
    assert (
        list(db_session.scalars(select(FollowUp.due_at).order_by(FollowUp.id))) == saved_due_dates
    )

    leads = list(db_session.scalars(select(Lead).where(Lead.owner_id == first.user.id)))
    quotations = list(
        db_session.scalars(select(Quotation).join(Lead).where(Lead.owner_id == first.user.id))
    )
    assert {lead.status for lead in leads} == set(LeadStatus)
    assert len({lead.source for lead in leads}) >= 6
    assert {quotation.status for quotation in quotations} == set(QuotationStatus)
    assert all(quotation.quote_number.startswith("Q-2026-9") for quotation in quotations)

    expected_group_counts = {
        FollowUpGroup.OVERDUE: 3,
        FollowUpGroup.TODAY: 3,
        FollowUpGroup.UPCOMING: 3,
        FollowUpGroup.COMPLETED: 3,
    }
    for group, expected_count in expected_group_counts.items():
        records, total = list_owned_followups(
            db_session,
            first.user.id,
            timezone_name=settings.demo_timezone,
            group=group,
            lead_id=None,
            now=FIXED_NOW,
        )
        assert total == expected_count
        assert len(records) == expected_count


def test_reset_restores_demo_data_and_preserves_every_other_owner(db_session: Session) -> None:
    settings = Settings(_env_file=None)
    seeded = seed_demo_data(db_session, settings, now=FIXED_NOW)
    original_password_hash = seeded.user.password_hash
    canonical_lead = db_session.scalar(
        select(Lead).where(
            Lead.owner_id == seeded.user.id,
            Lead.contact_name == DEMO_LEADS[0].contact_name,
        )
    )
    assert canonical_lead is not None
    canonical_id = canonical_lead.id
    canonical_lead.contact_name = "Modified demo record"
    manual_demo_lead = Lead(
        owner_id=seeded.user.id,
        contact_name="Manual demo-only record",
        estimated_value=Decimal("1.00"),
    )

    other_user = User(
        email=f"seed-owner-{uuid4()}@example.com",
        full_name="Seed Isolation Owner",
        password_hash="not-used",
        business_name="Seed Isolation Company",
        business_address="Private address",
        business_phone="+8801800000000",
        currency_code="USD",
        timezone="UTC",
    )
    other_lead = Lead(
        owner=other_user,
        contact_name="Other owner's preserved lead",
        estimated_value=Decimal("500.00"),
    )
    other_quote = Quotation(
        lead=other_lead,
        quote_number=f"Q-ISOL-{str(uuid4())[:8]}",
        status=QuotationStatus.DRAFT,
        issue_date=date(2026, 10, 5),
        valid_until=date(2026, 10, 19),
        subtotal=Decimal("50.00"),
        total=Decimal("50.00"),
        items=[
            QuotationItem(
                description="Preserved item",
                quantity=Decimal("1.000"),
                unit_price=Decimal("50.00"),
                line_total=Decimal("50.00"),
                sort_order=0,
            )
        ],
    )
    other_followup = FollowUp(
        lead=other_lead,
        due_at=FIXED_NOW + timedelta(days=2),
        note="Preserved follow-up",
    )
    db_session.add_all([manual_demo_lead, other_user, other_quote, other_followup])
    db_session.commit()
    preserved_ids = (
        other_user.id,
        other_lead.id,
        other_quote.id,
        other_quote.items[0].id,
        other_followup.id,
    )

    reset_anchor = FIXED_NOW + timedelta(days=30)
    reset = seed_demo_data(db_session, settings, reset=True, now=reset_anchor)

    assert reset.reset is True
    assert reset.user.id == seeded.user.id
    assert reset.user.password_hash == original_password_hash
    assert _owned_counts(db_session, reset.user.id) == (30, 8, 21, 12)
    restored = db_session.get(Lead, canonical_id)
    assert restored is not None
    assert restored.contact_name == DEMO_LEADS[0].contact_name
    assert (
        db_session.scalar(
            select(func.count())
            .select_from(Lead)
            .where(Lead.owner_id == reset.user.id, Lead.contact_name == "Manual demo-only record")
        )
        == 0
    )
    assert db_session.get(User, preserved_ids[0]) is not None
    assert db_session.get(Lead, preserved_ids[1]) is not None
    assert db_session.get(Quotation, preserved_ids[2]) is not None
    assert db_session.get(QuotationItem, preserved_ids[3]) is not None
    assert db_session.get(FollowUp, preserved_ids[4]) is not None

    today_records, _ = list_owned_followups(
        db_session,
        reset.user.id,
        timezone_name=settings.demo_timezone,
        group=FollowUpGroup.TODAY,
        lead_id=None,
        now=reset_anchor,
    )
    assert len(today_records) == 3


def test_production_reset_and_naive_seed_anchor_are_rejected_without_changes(
    db_session: Session,
) -> None:
    development_settings = Settings(_env_file=None)
    seeded = seed_demo_data(db_session, development_settings, now=FIXED_NOW)
    before = _owned_counts(db_session, seeded.user.id)
    production_settings = Settings(
        _env_file=None,
        environment="production",
        secret_key="a-private-production-signing-key-for-tests",
        database_url="postgresql+psycopg://clientflow@db.example.com/clientflow",
        cors_origins="https://clientflow.example.com",
        demo_user_password="a-production-only-demo-password",
    )

    with pytest.raises(RuntimeError, match="disabled in production"):
        seed_demo_data(db_session, production_settings, reset=True, now=FIXED_NOW)
    assert _owned_counts(db_session, seeded.user.id) == before

    with pytest.raises(ValueError, match="timezone information"):
        seed_demo_data(db_session, development_settings, now=datetime(2026, 10, 5, 6, 0))
    assert _owned_counts(db_session, seeded.user.id) == before
