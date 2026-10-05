from datetime import datetime, time, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.followup import FollowUp
from app.models.lead import Lead
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


def create_lead(
    client: TestClient,
    headers: dict[str, str],
    name: str = "Follow-up Client",
) -> dict:
    response = client.post(
        "/api/v1/leads",
        headers=headers,
        json={"contact_name": name, "estimated_value": "100.00"},
    )
    assert response.status_code == 201
    return response.json()


def local_due(day_offset: int, hour: int = 10) -> str:
    target_date = datetime.now(DEMO_TIMEZONE).date() + timedelta(days=day_offset)
    return datetime.combine(target_date, time(hour, 0), tzinfo=DEMO_TIMEZONE).isoformat()


def create_followup(
    client: TestClient,
    headers: dict[str, str],
    lead_id: str,
    *,
    note: str,
    due_at: str,
) -> dict:
    response = client.post(
        f"/api/v1/leads/{lead_id}/follow-ups",
        headers=headers,
        json={"note": note, "due_at": due_at},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_normalizes_note_and_rejects_invalid_input(client: TestClient) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    created = create_followup(
        client,
        headers,
        lead["id"],
        note="  Call about the proposal  ",
        due_at=local_due(1),
    )

    blank_note = client.post(
        f"/api/v1/leads/{lead['id']}/follow-ups",
        headers=headers,
        json={"note": "   ", "due_at": local_due(1)},
    )
    missing_due = client.post(
        f"/api/v1/leads/{lead['id']}/follow-ups",
        headers=headers,
        json={"note": "Missing date"},
    )
    naive_due = client.post(
        f"/api/v1/leads/{lead['id']}/follow-ups",
        headers=headers,
        json={"note": "Missing timezone", "due_at": "2026-10-05T10:00:00"},
    )

    assert created["note"] == "Call about the proposal"
    assert created["is_completed"] is False
    assert blank_note.status_code == missing_due.status_code == naive_due.status_code == 422


def test_timezone_groups_and_deterministic_order(client: TestClient) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    overdue = create_followup(
        client, headers, lead["id"], note="Overdue", due_at=local_due(-1)
    )
    today_late = create_followup(
        client, headers, lead["id"], note="Today late", due_at=local_due(0, 17)
    )
    today_early = create_followup(
        client, headers, lead["id"], note="Today early", due_at=local_due(0, 9)
    )
    upcoming_late = create_followup(
        client, headers, lead["id"], note="Upcoming late", due_at=local_due(2)
    )
    upcoming_early = create_followup(
        client, headers, lead["id"], note="Upcoming early", due_at=local_due(1)
    )

    overdue_group = client.get("/api/v1/follow-ups?group=overdue", headers=headers).json()
    today_group = client.get("/api/v1/follow-ups?group=today", headers=headers).json()
    upcoming_group = client.get("/api/v1/follow-ups?group=upcoming", headers=headers).json()

    assert [item["id"] for item in overdue_group["items"]] == [overdue["id"]]
    assert [item["id"] for item in today_group["items"]] == [
        today_early["id"],
        today_late["id"],
    ]
    assert [item["id"] for item in upcoming_group["items"]] == [
        upcoming_early["id"],
        upcoming_late["id"],
    ]


def test_edit_incomplete_and_complete_idempotently(
    client: TestClient,
    db_session: Session,
) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    followup = create_followup(
        client, headers, lead["id"], note="Initial note", due_at=local_due(0)
    )

    edited = client.patch(
        f"/api/v1/follow-ups/{followup['id']}",
        headers=headers,
        json={"note": "Updated note", "due_at": local_due(1)},
    )
    first_completion = client.patch(
        f"/api/v1/follow-ups/{followup['id']}/complete",
        headers=headers,
    )
    repeated_completion = client.patch(
        f"/api/v1/follow-ups/{followup['id']}/complete",
        headers=headers,
    )
    edit_completed = client.patch(
        f"/api/v1/follow-ups/{followup['id']}",
        headers=headers,
        json={"note": "Too late"},
    )
    completed_group = client.get("/api/v1/follow-ups?group=completed", headers=headers).json()

    assert edited.status_code == 200
    assert edited.json()["note"] == "Updated note"
    assert first_completion.status_code == repeated_completion.status_code == 200
    assert first_completion.json()["completed_at"] is not None
    assert repeated_completion.json()["completed_at"].rstrip("Z") == first_completion.json()[
        "completed_at"
    ].rstrip("Z")
    assert edit_completed.status_code == 409
    assert completed_group["total"] == 1
    assert completed_group["items"][0]["id"] == followup["id"]
    saved = db_session.get(FollowUp, UUID(followup["id"]))
    assert saved is not None and saved.is_completed is True


def test_cross_user_followup_access_is_hidden(client: TestClient, db_session: Session) -> None:
    demo_headers = auth_headers(client)
    other_user = User(
        email="followup-owner@clientflow.app",
        full_name="Follow-up Owner",
        password_hash=hash_password("other-password"),
        is_active=True,
        business_name="Private Follow-up Company",
        business_address="Private address",
        business_phone="+8801800000000",
        currency_code="BDT",
        timezone="Asia/Dhaka",
    )
    db_session.add(other_user)
    db_session.flush()
    other_lead = Lead(
        owner_id=other_user.id,
        contact_name="Private Follow-up Lead",
        estimated_value=Decimal("100.00"),
    )
    db_session.add(other_lead)
    db_session.commit()
    other_token, _ = create_access_token(other_user.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    followup = create_followup(
        client,
        other_headers,
        str(other_lead.id),
        note="Private reminder",
        due_at=local_due(1),
    )

    create_on_other = client.post(
        f"/api/v1/leads/{other_lead.id}/follow-ups",
        headers=demo_headers,
        json={"note": "Trespass", "due_at": local_due(1)},
    )
    edit = client.patch(
        f"/api/v1/follow-ups/{followup['id']}",
        headers=demo_headers,
        json={"note": "Trespass"},
    )
    complete = client.patch(
        f"/api/v1/follow-ups/{followup['id']}/complete",
        headers=demo_headers,
    )
    filtered_list = client.get(
        f"/api/v1/follow-ups?lead_id={other_lead.id}",
        headers=demo_headers,
    )
    own_list = client.get("/api/v1/follow-ups", headers=demo_headers).json()

    assert create_on_other.status_code == 404
    assert edit.status_code == complete.status_code == filtered_list.status_code == 404
    assert own_list["total"] == 0
