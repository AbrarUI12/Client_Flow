from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import LeadStatus, QuotationStatus
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.quotation import Quotation
from app.models.user import User

DEMO_EMAIL = "demo@clientflow.app"
DEMO_PASSWORD = "development-only-change-me"
DEMO_TIMEZONE = ZoneInfo("Asia/Dhaka")


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def local_instant(day_offset: int, hour: int = 10) -> datetime:
    local_date = datetime.now(DEMO_TIMEZONE).date() + timedelta(days=day_offset)
    return datetime.combine(local_date, time(hour), tzinfo=DEMO_TIMEZONE).astimezone(UTC)


def quotation(lead: Lead, number: str, quotation_status: QuotationStatus, total: str) -> Quotation:
    return Quotation(
        lead=lead,
        quote_number=number,
        status=quotation_status,
        issue_date=date.today(),
        valid_until=date.today() + timedelta(days=14),
        subtotal=Decimal(total),
        total=Decimal(total),
    )


def test_dashboard_aggregates_owned_active_records(
    client: TestClient,
    db_session: Session,
) -> None:
    demo_user = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))
    assert demo_user is not None
    other_user = User(
        email="dashboard-owner@clientflow.app",
        full_name="Dashboard Owner",
        password_hash=hash_password("other-password"),
        is_active=True,
        business_name="Other Dashboard Company",
        business_address="Other address",
        business_phone="+8801800000000",
        currency_code="BDT",
        timezone="Asia/Dhaka",
    )
    db_session.add(other_user)
    db_session.flush()

    older_active = Lead(
        owner_id=demo_user.id,
        contact_name="Older Active Lead",
        status=LeadStatus.NEW,
        estimated_value=Decimal("100.00"),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    newer_active = Lead(
        owner_id=demo_user.id,
        contact_name="Newer Active Lead",
        status=LeadStatus.WON,
        estimated_value=Decimal("200.00"),
        created_at=datetime(2026, 2, 1, tzinfo=UTC),
        updated_at=datetime(2026, 2, 1, tzinfo=UTC),
    )
    archived = Lead(
        owner_id=demo_user.id,
        contact_name="Archived Lead",
        status=LeadStatus.LOST,
        is_archived=True,
        estimated_value=Decimal("300.00"),
    )
    foreign = Lead(
        owner_id=other_user.id,
        contact_name="Foreign Lead",
        status=LeadStatus.QUALIFIED,
        estimated_value=Decimal("400.00"),
    )
    db_session.add_all([older_active, newer_active, archived, foreign])
    db_session.flush()
    db_session.add_all(
        [
            quotation(older_active, "Q-DASH-0001", QuotationStatus.DRAFT, "100.00"),
            quotation(newer_active, "Q-DASH-0002", QuotationStatus.SENT, "200.50"),
            quotation(older_active, "Q-DASH-0003", QuotationStatus.ACCEPTED, "500.00"),
            quotation(archived, "Q-DASH-0004", QuotationStatus.DRAFT, "1000.00"),
            quotation(foreign, "Q-DASH-0005", QuotationStatus.DRAFT, "5000.00"),
            FollowUp(lead=older_active, note="Owned overdue", due_at=local_instant(-1)),
            FollowUp(lead=newer_active, note="Owned upcoming", due_at=local_instant(1)),
            FollowUp(lead=archived, note="Archived overdue", due_at=local_instant(-2)),
            FollowUp(lead=foreign, note="Foreign overdue", due_at=local_instant(-2)),
            FollowUp(
                lead=older_active,
                note="Completed overdue",
                due_at=local_instant(-3),
                is_completed=True,
                completed_at=local_instant(-1),
            ),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/dashboard/summary", headers=auth_headers(client))

    assert response.status_code == 200
    summary = response.json()
    assert summary["total_leads"] == 2
    assert summary["open_quotation_count"] == 2
    assert summary["open_quotation_value"] == "300.50"
    assert summary["overdue_followup_count"] == 1
    assert summary["pipeline_counts"] == {
        "NEW": 1,
        "CONTACTED": 0,
        "QUALIFIED": 0,
        "QUOTED": 0,
        "WON": 1,
        "LOST": 0,
    }
    assert [item["note"] for item in summary["overdue_followups"]] == ["Owned overdue"]
    assert [item["note"] for item in summary["upcoming_followups"]] == ["Owned upcoming"]
    assert [item["contact_name"] for item in summary["recent_leads"]] == [
        "Newer Active Lead",
        "Older Active Lead",
    ]


def test_dashboard_requires_authentication_and_returns_stable_empty_shape(
    client: TestClient,
    db_session: Session,
) -> None:
    assert client.get("/api/v1/dashboard/summary").status_code == 401
    headers = auth_headers(client)
    first = client.get("/api/v1/dashboard/summary", headers=headers)
    second = client.get("/api/v1/dashboard/summary", headers=headers)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["total_leads"] == 0
    assert first.json()["open_quotation_value"] == "0.00"
