from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.enums import LeadSource, LeadStatus
from app.models.lead import Lead
from app.models.user import User

DEMO_EMAIL = "demo@clientflow.app"
DEMO_PASSWORD = "development-only-change-me"


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
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "contact_name": "John Smith",
        "company": "Acme Ltd",
        "email": "john@acme.example",
        "phone": "+8801700000000",
        "source": "REFERRAL",
        "status": "QUALIFIED",
        "estimated_value": "2500.00",
        "notes": "Interested in a website redesign.",
    }
    payload.update(overrides)
    response = client.post("/api/v1/leads", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_valid_lead_normalizes_fields(client: TestClient) -> None:
    headers = auth_headers(client)
    lead = create_lead(
        client,
        headers,
        contact_name="  John Smith  ",
        company="  Acme Ltd  ",
        email="  JOHN@ACME.EXAMPLE  ",
    )

    assert lead["contact_name"] == "John Smith"
    assert lead["company"] == "Acme Ltd"
    assert lead["email"] == "john@acme.example"
    assert lead["estimated_value"] == "2500.00"
    assert lead["is_archived"] is False


def test_invalid_lead_data_and_pagination_are_rejected(client: TestClient) -> None:
    headers = auth_headers(client)

    blank_name = client.post("/api/v1/leads", headers=headers, json={"contact_name": "   "})
    invalid_email = client.post(
        "/api/v1/leads",
        headers=headers,
        json={"contact_name": "Valid Name", "email": "not-an-email"},
    )
    negative_value = client.post(
        "/api/v1/leads",
        headers=headers,
        json={"contact_name": "Valid Name", "estimated_value": "-0.01"},
    )
    invalid_page = client.get("/api/v1/leads?page=0&page_size=101", headers=headers)
    lead = create_lead(client, headers)
    null_status = client.patch(
        f"/api/v1/leads/{lead['id']}",
        headers=headers,
        json={"status": None},
    )

    assert blank_name.status_code == 422
    assert invalid_email.status_code == 422
    assert negative_value.status_code == 422
    assert invalid_page.status_code == 422
    assert null_status.status_code == 422


def test_list_search_filter_and_stable_pagination(client: TestClient) -> None:
    headers = auth_headers(client)
    create_lead(client, headers, contact_name="Alice Brown", company="Northwind", source="WEBSITE")
    create_lead(client, headers, contact_name="Bob Stone", company="Blue Ocean", source="REFERRAL")
    create_lead(
        client,
        headers,
        contact_name="Carla Jones",
        company="Northwind Labs",
        source="WEBSITE",
        status="NEW",
    )
    create_lead(client, headers, contact_name="Derek Lee", company="Dawn", source="PHONE")
    create_lead(client, headers, contact_name="Eva Ray", company="Evergreen", source="EMAIL")

    search = client.get("/api/v1/leads?search=northwind", headers=headers).json()
    filtered = client.get(
        "/api/v1/leads?status=NEW&source=WEBSITE",
        headers=headers,
    ).json()
    first_page = client.get("/api/v1/leads?page=1&page_size=2", headers=headers).json()
    repeated_page = client.get("/api/v1/leads?page=1&page_size=2", headers=headers).json()
    second_page = client.get("/api/v1/leads?page=2&page_size=2", headers=headers).json()

    assert search["total"] == 2
    assert {item["company"] for item in search["items"]} == {"Northwind", "Northwind Labs"}
    assert filtered["total"] == 1
    assert filtered["items"][0]["contact_name"] == "Carla Jones"
    assert first_page["total"] == 5
    assert first_page["pages"] == 3
    assert first_page["items"] == repeated_page["items"]
    assert {item["id"] for item in first_page["items"]}.isdisjoint(
        {item["id"] for item in second_page["items"]}
    )


def test_update_archive_and_exclude_archived_lead(client: TestClient) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)

    update = client.patch(
        f"/api/v1/leads/{lead['id']}",
        headers=headers,
        json={"status": "QUOTED", "estimated_value": "3200.50", "company": "Acme Group"},
    )
    archive = client.post(f"/api/v1/leads/{lead['id']}/archive", headers=headers)
    detail_after_archive = client.get(f"/api/v1/leads/{lead['id']}", headers=headers)
    listed = client.get("/api/v1/leads", headers=headers).json()

    assert update.status_code == 200
    assert update.json()["status"] == "QUOTED"
    assert update.json()["estimated_value"] == "3200.50"
    assert archive.status_code == 200
    assert archive.json()["is_archived"] is True
    assert detail_after_archive.status_code == 404
    assert listed["total"] == 0


def test_cross_user_lead_access_is_hidden(
    client: TestClient,
    db_session: Session,
) -> None:
    demo_user = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))
    assert demo_user is not None
    other_user = User(
        email="other@clientflow.app",
        full_name="Other Owner",
        password_hash=hash_password("other-password"),
        is_active=True,
        business_name="Other Company",
        business_address="Other address",
        business_phone="+8801800000000",
        currency_code="BDT",
        timezone="Asia/Dhaka",
    )
    db_session.add(other_user)
    db_session.flush()
    other_lead = Lead(
        owner_id=other_user.id,
        contact_name="Private Contact",
        source=LeadSource.OTHER,
        status=LeadStatus.NEW,
        estimated_value=Decimal("10.00"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(other_lead)
    db_session.commit()

    demo_headers = auth_headers(client)
    other_token, _ = create_access_token(other_user.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    assert client.get(f"/api/v1/leads/{other_lead.id}", headers=other_headers).status_code == 200
    own_list = client.get("/api/v1/leads", headers=demo_headers).json()
    view = client.get(f"/api/v1/leads/{other_lead.id}", headers=demo_headers)
    update = client.patch(
        f"/api/v1/leads/{other_lead.id}",
        headers=demo_headers,
        json={"status": "WON"},
    )
    archive = client.post(f"/api/v1/leads/{other_lead.id}/archive", headers=demo_headers)

    assert own_list["total"] == 0
    assert view.status_code == update.status_code == archive.status_code == 404
    assert view.json() == update.json() == archive.json()
