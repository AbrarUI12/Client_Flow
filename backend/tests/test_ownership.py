from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.enums import LeadStatus
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.quotation import Quotation
from app.models.user import User

DEMO_EMAIL = "demo@clientflow.app"
DEMO_PASSWORD = "development-only-change-me"
DHAKA = ZoneInfo("Asia/Dhaka")


@dataclass
class Tenant:
    headers: dict[str, str]
    lead: dict
    draft: dict
    sent: dict
    followup: dict


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def quotation_payload(notes: str = "Original notes") -> dict:
    return {
        "issue_date": date.today().isoformat(),
        "valid_until": (date.today() + timedelta(days=14)).isoformat(),
        "notes": notes,
        "items": [{"description": "Service", "quantity": "1.000", "unit_price": "100.00"}],
    }


def overdue_due_at() -> str:
    yesterday = datetime.now(DHAKA).date() - timedelta(days=1)
    return datetime(yesterday.year, yesterday.month, yesterday.day, 10, tzinfo=DHAKA).isoformat()


def populate_tenant(client: TestClient, headers: dict[str, str], name: str) -> Tenant:
    lead = client.post(
        "/api/v1/leads",
        headers=headers,
        json={"contact_name": name, "status": "QUALIFIED", "estimated_value": "100.00"},
    ).json()
    draft = client.post(
        f"/api/v1/leads/{lead['id']}/quotations", headers=headers, json=quotation_payload()
    ).json()
    sent = client.post(
        f"/api/v1/leads/{lead['id']}/quotations", headers=headers, json=quotation_payload()
    ).json()
    sent = client.patch(
        f"/api/v1/quotations/{sent['id']}/status", headers=headers, json={"status": "SENT"}
    ).json()
    followup = client.post(
        f"/api/v1/leads/{lead['id']}/follow-ups",
        headers=headers,
        json={"note": "Original reminder", "due_at": overdue_due_at()},
    ).json()
    return Tenant(headers=headers, lead=lead, draft=draft, sent=sent, followup=followup)


@pytest.fixture
def other_tenant(client: TestClient, db_session: Session) -> Tenant:
    other = User(
        email="tenant-b@clientflow.app",
        full_name="Tenant B",
        password_hash=hash_password("tenant-b-password"),
        business_name="Tenant B Studio",
        business_address="Tenant B address",
        business_phone="+8801800000000",
        currency_code="BDT",
        timezone="Asia/Dhaka",
    )
    db_session.add(other)
    db_session.commit()
    token, _ = create_access_token(other.id)
    return populate_tenant(client, {"Authorization": f"Bearer {token}"}, "Tenant B Client")


def test_foreign_records_are_indistinguishable_from_missing_ones_and_stay_unchanged(
    client: TestClient, other_tenant: Tenant
) -> None:
    headers = auth_headers(client)
    foreign = other_tenant
    lead_id, draft_id = foreign.lead["id"], foreign.draft["id"]
    sent_id, followup_id = foreign.sent["id"], foreign.followup["id"]
    operations = [
        ("GET", "/api/v1/leads/{id}", lead_id, None),
        ("PATCH", "/api/v1/leads/{id}", lead_id, {"status": "WON", "notes": "hijacked"}),
        ("POST", "/api/v1/leads/{id}/archive", lead_id, None),
        ("GET", "/api/v1/leads/{id}/quotations", lead_id, None),
        ("POST", "/api/v1/leads/{id}/quotations", lead_id, quotation_payload("hijacked")),
        (
            "POST",
            "/api/v1/leads/{id}/follow-ups",
            lead_id,
            {"note": "hijacked", "due_at": overdue_due_at()},
        ),
        ("GET", "/api/v1/follow-ups?lead_id={id}", lead_id, None),
        ("GET", "/api/v1/quotations/{id}", draft_id, None),
        ("PATCH", "/api/v1/quotations/{id}", draft_id, {"notes": "hijacked"}),
        ("PATCH", "/api/v1/quotations/{id}/status", draft_id, {"status": "SENT"}),
        ("PATCH", "/api/v1/quotations/{id}/status", sent_id, {"status": "ACCEPTED"}),
        ("PATCH", "/api/v1/quotations/{id}/status", sent_id, {"status": "REJECTED"}),
        ("GET", "/api/v1/quotations/{id}/pdf", sent_id, None),
        ("PATCH", "/api/v1/follow-ups/{id}", followup_id, {"note": "hijacked"}),
        ("PATCH", "/api/v1/follow-ups/{id}/complete", followup_id, None),
    ]

    for method, template, foreign_id, body in operations:
        attempt = client.request(
            method, template.format(id=foreign_id), headers=headers, json=body
        )
        missing = client.request(
            method, template.format(id=uuid4()), headers=headers, json=body
        )
        assert attempt.status_code == 404, (method, template)
        assert attempt.json() == missing.json(), (method, template)

    owner = foreign.headers
    lead = client.get(f"/api/v1/leads/{lead_id}", headers=owner).json()
    draft = client.get(f"/api/v1/quotations/{draft_id}", headers=owner).json()
    sent = client.get(f"/api/v1/quotations/{sent_id}", headers=owner).json()
    followups = client.get(f"/api/v1/follow-ups?lead_id={lead_id}", headers=owner).json()
    quotes = client.get(f"/api/v1/leads/{lead_id}/quotations", headers=owner).json()

    assert (lead["status"], lead["notes"], lead["is_archived"]) == ("QUOTED", None, False)
    assert (draft["status"], draft["notes"]) == ("DRAFT", "Original notes")
    assert sent["status"] == "SENT"
    assert quotes["total"] == 2
    assert followups["total"] == 1
    assert followups["items"][0]["note"] == "Original reminder"
    assert followups["items"][0]["is_completed"] is False


def test_lists_dashboard_and_exports_contain_only_the_callers_records(
    client: TestClient, other_tenant: Tenant
) -> None:
    headers = auth_headers(client)
    own = populate_tenant(client, headers, "Demo Own Client")

    leads = client.get("/api/v1/leads", headers=headers).json()
    quotes = client.get("/api/v1/quotations", headers=headers).json()
    followups = client.get("/api/v1/follow-ups", headers=headers).json()
    dashboard = client.get("/api/v1/dashboard/summary", headers=headers).json()
    csv_text = client.get("/api/v1/leads/export", headers=headers).content.decode("utf-8-sig")

    assert [item["id"] for item in leads["items"]] == [own.lead["id"]]
    assert {item["id"] for item in quotes["items"]} == {own.draft["id"], own.sent["id"]}
    assert [item["id"] for item in followups["items"]] == [own.followup["id"]]
    assert dashboard["total_leads"] == 1
    assert dashboard["open_quotation_count"] == 2
    assert "Demo Own Client" in csv_text
    assert "Tenant B Client" not in csv_text


def test_archived_leads_hide_their_quotations_and_follow_ups_everywhere(
    client: TestClient, db_session: Session
) -> None:
    headers = auth_headers(client)
    own = populate_tenant(client, headers, "Soon Archived Client")

    def list_totals() -> tuple[int, int, int]:
        quotes = client.get("/api/v1/quotations", headers=headers).json()["total"]
        followups = client.get("/api/v1/follow-ups", headers=headers).json()["total"]
        overdue = client.get("/api/v1/follow-ups?group=overdue", headers=headers).json()["total"]
        return quotes, followups, overdue

    def dashboard_totals() -> tuple[int, int]:
        summary = client.get("/api/v1/dashboard/summary", headers=headers).json()
        return summary["open_quotation_count"], summary["overdue_followup_count"]

    assert list_totals() == (2, 1, 1)
    assert dashboard_totals() == (2, 1)

    archive = client.post(f"/api/v1/leads/{own.lead['id']}/archive", headers=headers)
    assert archive.status_code == 200

    # The dashboard and the pages its cards link to agree after archiving.
    assert list_totals() == (0, 0, 0)
    assert dashboard_totals() == (0, 0)
    hidden_requests = [
        ("GET", f"/api/v1/quotations/{own.draft['id']}", None, "QUOTATION_NOT_FOUND"),
        ("PATCH", f"/api/v1/quotations/{own.draft['id']}", {"notes": "x"}, "QUOTATION_NOT_FOUND"),
        (
            "PATCH",
            f"/api/v1/quotations/{own.sent['id']}/status",
            {"status": "ACCEPTED"},
            "QUOTATION_NOT_FOUND",
        ),
        ("GET", f"/api/v1/quotations/{own.sent['id']}/pdf", None, "QUOTATION_NOT_FOUND"),
        (
            "PATCH",
            f"/api/v1/follow-ups/{own.followup['id']}",
            {"note": "x"},
            "FOLLOW_UP_NOT_FOUND",
        ),
        (
            "PATCH",
            f"/api/v1/follow-ups/{own.followup['id']}/complete",
            None,
            "FOLLOW_UP_NOT_FOUND",
        ),
    ]
    for method, url, body, code in hidden_requests:
        response = client.request(method, url, headers=headers, json=body)
        assert response.status_code == 404, (method, url)
        assert response.json()["detail"]["code"] == code

    # Archived records remain stored and the hidden lead was not silently marked won.
    lead = db_session.get(Lead, own.lead["id"])
    assert lead is not None
    db_session.refresh(lead)
    assert (lead.is_archived, lead.status) == (True, LeadStatus.QUOTED)
    stored_quotes = db_session.scalar(
        select(func.count()).select_from(Quotation).where(Quotation.lead_id == lead.id)
    )
    stored_followups = db_session.scalar(
        select(func.count()).select_from(FollowUp).where(FollowUp.lead_id == lead.id)
    )
    assert (stored_quotes, stored_followups) == (2, 1)
