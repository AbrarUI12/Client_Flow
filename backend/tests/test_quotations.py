from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.enums import LeadStatus
from app.models.lead import Lead
from app.models.quotation import QuotationItem
from app.models.user import User
from app.schemas.quotation import QuotationItemInput
from app.services.quotation_service import calculate_quotation

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
    contact_name: str = "Quotation Client",
) -> dict:
    response = client.post(
        "/api/v1/leads",
        headers=headers,
        json={
            "contact_name": contact_name,
            "company": "Example Studio",
            "email": "quote-client@example.com",
            "status": "QUALIFIED",
            "estimated_value": "5000.00",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def quotation_payload(**overrides: object) -> dict:
    payload: dict[str, object] = {
        "issue_date": date.today().isoformat(),
        "valid_until": (date.today() + timedelta(days=14)).isoformat(),
        "discount_percent": "10.00",
        "tax_percent": "7.50",
        "notes": "A carefully calculated proposal.",
        "items": [
            {
                "description": "Design system",
                "quantity": "2.345",
                "unit_price": "19.99",
            },
            {
                "description": "Implementation",
                "quantity": "1.000",
                "unit_price": "10.00",
            },
        ],
    }
    payload.update(overrides)
    return payload


def create_quote(
    client: TestClient,
    headers: dict[str, str],
    lead_id: str,
    **overrides: object,
) -> dict:
    response = client.post(
        f"/api/v1/leads/{lead_id}/quotations",
        headers=headers,
        json=quotation_payload(**overrides),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_calculation_rounds_each_money_result_half_up() -> None:
    totals = calculate_quotation(
        [
            QuotationItemInput(
                description="Rounding boundary",
                quantity=Decimal("1.001"),
                unit_price=Decimal("5.00"),
            )
        ],
        Decimal("10.00"),
        Decimal("7.50"),
    )

    assert totals.items[0].line_total == Decimal("5.01")
    assert totals.subtotal == Decimal("5.01")
    assert totals.discount_amount == Decimal("0.50")
    assert totals.tax_amount == Decimal("0.34")
    assert totals.total == Decimal("4.85")


def test_create_calculates_authoritative_totals_and_rejects_client_totals(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    quote = create_quote(client, headers, lead["id"])

    assert [item["line_total"] for item in quote["items"]] == ["46.88", "10.00"]
    assert quote["subtotal"] == "56.88"
    assert quote["discount_amount"] == "5.69"
    assert quote["tax_amount"] == "3.84"
    assert quote["total"] == "55.03"
    assert quote["status"] == "DRAFT"
    assert quote["quote_number"].startswith(f"Q-{date.today().year}-")

    supplied_total = quotation_payload(total="0.01", subtotal="0.01")
    response = client.post(
        f"/api/v1/leads/{lead['id']}/quotations",
        headers=headers,
        json=supplied_total,
    )
    assert response.status_code == 422


def test_invalid_items_percentages_and_dates_are_rejected(client: TestClient) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    invalid_payloads = [
        quotation_payload(items=[]),
        quotation_payload(items=[{"description": "  ", "quantity": "1", "unit_price": "1"}]),
        quotation_payload(items=[{"description": "Bad", "quantity": "0", "unit_price": "1"}]),
        quotation_payload(items=[{"description": "Bad", "quantity": "-1", "unit_price": "1"}]),
        quotation_payload(items=[{"description": "Bad", "quantity": "1", "unit_price": "-0.01"}]),
        quotation_payload(discount_percent="100.01"),
        quotation_payload(tax_percent="-0.01"),
        quotation_payload(
            issue_date=date.today().isoformat(),
            valid_until=(date.today() - timedelta(days=1)).isoformat(),
        ),
    ]

    for payload in invalid_payloads:
        response = client.post(
            f"/api/v1/leads/{lead['id']}/quotations",
            headers=headers,
            json=payload,
        )
        assert response.status_code == 422, response.text


def test_unique_numbers_search_filter_and_pagination(client: TestClient) -> None:
    headers = auth_headers(client)
    alpha_lead = create_lead(client, headers, "Alpha Search Client")
    beta_lead = create_lead(client, headers, "Beta Client")
    first = create_quote(client, headers, alpha_lead["id"])
    second = create_quote(client, headers, beta_lead["id"])

    assert first["quote_number"] != second["quote_number"]

    search = client.get("/api/v1/quotations?search=Alpha", headers=headers).json()
    filtered = client.get("/api/v1/quotations?status=DRAFT", headers=headers).json()
    first_page = client.get("/api/v1/quotations?page=1&page_size=1", headers=headers).json()
    second_page = client.get("/api/v1/quotations?page=2&page_size=1", headers=headers).json()
    lead_quotes = client.get(
        f"/api/v1/leads/{alpha_lead['id']}/quotations",
        headers=headers,
    ).json()

    assert search["total"] == 1
    assert search["items"][0]["lead"]["contact_name"] == "Alpha Search Client"
    assert filtered["total"] == 2
    assert first_page["pages"] == 2
    assert first_page["items"][0]["id"] != second_page["items"][0]["id"]
    assert lead_quotes["total"] == 1
    assert lead_quotes["items"][0]["id"] == first["id"]


def test_draft_edit_replaces_items_and_recalculates(
    client: TestClient,
    db_session: Session,
) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    quote = create_quote(client, headers, lead["id"])
    original_item_ids = {UUID(item["id"]) for item in quote["items"]}

    response = client.patch(
        f"/api/v1/quotations/{quote['id']}",
        headers=headers,
        json={
            "discount_percent": "0",
            "tax_percent": "5",
            "notes": "Revised scope",
            "items": [
                {
                    "description": "Replacement item",
                    "quantity": "3.000",
                    "unit_price": "20.00",
                }
            ],
        },
    )

    assert response.status_code == 200, response.text
    edited = response.json()
    assert len(edited["items"]) == 1
    assert edited["items"][0]["description"] == "Replacement item"
    assert edited["subtotal"] == "60.00"
    assert edited["tax_amount"] == "3.00"
    assert edited["total"] == "63.00"
    assert edited["notes"] == "Revised scope"
    assert UUID(edited["items"][0]["id"]) not in original_item_ids
    remaining_old_items = db_session.scalar(
        select(func.count()).select_from(QuotationItem).where(QuotationItem.id.in_(original_item_ids))
    )
    assert remaining_old_items == 0


def test_status_transitions_edit_lock_and_acceptance_updates_lead(
    client: TestClient,
    db_session: Session,
) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    quote = create_quote(client, headers, lead["id"])

    invalid = client.patch(
        f"/api/v1/quotations/{quote['id']}/status",
        headers=headers,
        json={"status": "ACCEPTED"},
    )
    sent = client.patch(
        f"/api/v1/quotations/{quote['id']}/status",
        headers=headers,
        json={"status": "SENT"},
    )
    edit_sent = client.patch(
        f"/api/v1/quotations/{quote['id']}",
        headers=headers,
        json={"notes": "This must be rejected"},
    )
    accepted = client.patch(
        f"/api/v1/quotations/{quote['id']}/status",
        headers=headers,
        json={"status": "ACCEPTED"},
    )
    terminal = client.patch(
        f"/api/v1/quotations/{quote['id']}/status",
        headers=headers,
        json={"status": "REJECTED"},
    )

    assert invalid.status_code == 409
    assert sent.status_code == 200
    assert sent.json()["sent_at"] is not None
    assert edit_sent.status_code == 409
    assert accepted.status_code == 200
    assert accepted.json()["accepted_at"] is not None
    assert terminal.status_code == 409
    db_session.expire_all()
    saved_lead = db_session.get(Lead, UUID(lead["id"]))
    assert saved_lead is not None
    assert saved_lead.status == LeadStatus.WON


def test_rejected_quote_does_not_mark_lead_lost(client: TestClient, db_session: Session) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    quote = create_quote(client, headers, lead["id"])
    client.patch(
        f"/api/v1/quotations/{quote['id']}/status",
        headers=headers,
        json={"status": "SENT"},
    )
    rejected = client.patch(
        f"/api/v1/quotations/{quote['id']}/status",
        headers=headers,
        json={"status": "REJECTED"},
    )

    assert rejected.status_code == 200
    assert rejected.json()["rejected_at"] is not None
    db_session.expire_all()
    saved_lead = db_session.get(Lead, UUID(lead["id"]))
    assert saved_lead is not None
    assert saved_lead.status == LeadStatus.QUOTED
    assert saved_lead.status != LeadStatus.LOST


def test_cross_user_quotation_access_is_hidden(
    client: TestClient,
    db_session: Session,
) -> None:
    demo_headers = auth_headers(client)
    other_user = User(
        email="quotation-owner@clientflow.app",
        full_name="Quotation Owner",
        password_hash=hash_password("other-password"),
        is_active=True,
        business_name="Private Quote Company",
        business_address="Private address",
        business_phone="+8801800000000",
        currency_code="BDT",
        timezone="Asia/Dhaka",
    )
    db_session.add(other_user)
    db_session.flush()
    other_lead = Lead(
        owner_id=other_user.id,
        contact_name="Private Quote Lead",
        estimated_value=Decimal("100.00"),
    )
    db_session.add(other_lead)
    db_session.commit()
    other_token, _ = create_access_token(other_user.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    quote = create_quote(client, other_headers, str(other_lead.id))

    create_on_other = client.post(
        f"/api/v1/leads/{other_lead.id}/quotations",
        headers=demo_headers,
        json=quotation_payload(),
    )
    lead_list = client.get(
        f"/api/v1/leads/{other_lead.id}/quotations",
        headers=demo_headers,
    )
    view = client.get(f"/api/v1/quotations/{quote['id']}", headers=demo_headers)
    edit = client.patch(
        f"/api/v1/quotations/{quote['id']}",
        headers=demo_headers,
        json={"notes": "Trespass"},
    )
    transition = client.patch(
        f"/api/v1/quotations/{quote['id']}/status",
        headers=demo_headers,
        json={"status": "SENT"},
    )
    own_list = client.get("/api/v1/quotations", headers=demo_headers).json()

    assert create_on_other.status_code == 404
    assert lead_list.status_code == 404
    assert view.status_code == edit.status_code == transition.status_code == 404
    assert own_list["total"] == 0
