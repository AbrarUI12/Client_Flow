import csv
import io
from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
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
) -> dict:
    payload: dict[str, object] = {
        "contact_name": "Export Client",
        "company": "Export Studio",
        "email": "export@example.com",
        "phone": "+8801700000000",
        "source": "LINKEDIN",
        "status": "QUALIFIED",
        "estimated_value": "1234.50",
        "notes": "Export test lead",
    }
    payload.update(overrides)
    response = client.post("/api/v1/leads", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def create_quote(
    client: TestClient,
    headers: dict[str, str],
    lead_id: str,
    items: list[dict[str, str]],
) -> dict:
    response = client.post(
        f"/api/v1/leads/{lead_id}/quotations",
        headers=headers,
        json={
            "issue_date": date.today().isoformat(),
            "valid_until": (date.today() + timedelta(days=14)).isoformat(),
            "discount_percent": "10.00",
            "tax_percent": "7.50",
            "notes": "Payment due within fourteen days.\nThank you for your business.",
            "items": items,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_lead_csv_is_owned_complete_escaped_and_formula_safe(
    client: TestClient,
    db_session: Session,
) -> None:
    headers = auth_headers(client)
    exported = create_lead(
        client,
        headers,
        contact_name="=2+5",
        company='Café, "North"',
        phone="+8801700000000",
        notes="First line, with comma\nSecond line with \"quotes\" and বাংলা",
    )
    archived = create_lead(client, headers, contact_name="Archived Export Lead")
    archive_response = client.post(f"/api/v1/leads/{archived['id']}/archive", headers=headers)
    assert archive_response.status_code == 200

    other_user = User(
        email="csv-owner@example.com",
        full_name="CSV Owner",
        password_hash=hash_password("other-password"),
        is_active=True,
        business_name="Other Company",
        business_address="Other address",
        business_phone="+8801800000000",
        currency_code="USD",
        timezone="UTC",
    )
    db_session.add(other_user)
    db_session.flush()
    db_session.add(
        Lead(
            owner_id=other_user.id,
            contact_name="Private Export Lead",
            estimated_value=Decimal("999.99"),
        )
    )
    db_session.commit()

    response = client.get("/api/v1/leads/export", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"].startswith(
        'attachment; filename="clientflow-leads-'
    )
    assert response.content.startswith(b"\xef\xbb\xbf")
    decoded = response.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    assert reader.fieldnames == [
        "Contact Name",
        "Company",
        "Email",
        "Phone",
        "Source",
        "Status",
        "Estimated Value",
        "Currency",
        "Notes",
        "Created At",
        "Updated At",
    ]
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]
    assert row["Contact Name"] == "'=2+5"
    assert row["Company"] == 'Café, "North"'
    assert row["Phone"] == "'+8801700000000"
    assert row["Source"] == "LinkedIn"
    assert row["Status"] == "Qualified"
    assert row["Estimated Value"] == "1234.50"
    assert row["Currency"] == "BDT"
    assert row["Notes"] == "First line, with comma\nSecond line with \"quotes\" and বাংলা"
    assert row["Created At"].endswith("+06")
    assert str(exported["id"]) not in decoded
    assert "Archived Export Lead" not in decoded
    assert "Private Export Lead" not in decoded

    anonymous = client.get("/api/v1/leads/export")
    assert anonymous.status_code == 401


def test_quotation_pdf_uses_stored_totals_and_professional_content(client: TestClient) -> None:
    headers = auth_headers(client)
    lead = create_lead(
        client,
        headers,
        contact_name="PDF Client",
        company="PDF Client Company",
    )
    quote = create_quote(
        client,
        headers,
        lead["id"],
        [
            {"description": "Design system", "quantity": "2.345", "unit_price": "19.99"},
            {"description": "Implementation", "quantity": "1.000", "unit_price": "10.00"},
        ],
    )

    response = client.get(f"/api/v1/quotations/{quote['id']}/pdf", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="quotation-{quote["quote_number"]}.pdf"'
    )
    assert response.content.startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(response.content))
    assert len(reader.pages) == 1
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "ClientFlow Demo Company" in text
    assert "PDF Client" in text
    assert quote["quote_number"] in text
    assert "Design system" in text
    assert "BDT 56.88" in text
    assert "BDT 55.03" in text
    assert "Payment due within fourteen days." in text


def test_long_quotation_pdf_paginates_and_cross_user_access_is_hidden(
    client: TestClient,
    db_session: Session,
) -> None:
    demo_headers = auth_headers(client)
    lead = create_lead(client, demo_headers, contact_name="Long PDF Client")
    items = [
        {
            "description": f"Detailed project deliverable number {index:02d}",
            "quantity": "1.000",
            "unit_price": "10.00",
        }
        for index in range(1, 56)
    ]
    quote = create_quote(client, demo_headers, lead["id"], items)
    response = client.get(f"/api/v1/quotations/{quote['id']}/pdf", headers=demo_headers)
    reader = PdfReader(io.BytesIO(response.content))
    text = "\n".join(page.extract_text() for page in reader.pages)

    assert response.status_code == 200
    assert len(reader.pages) >= 2
    assert "Detailed project deliverable number 01" in text
    assert "Detailed project deliverable number 55" in text
    assert "BDT 532.13" in text

    other_user = User(
        email="pdf-owner@example.com",
        full_name="PDF Owner",
        password_hash=hash_password("other-password"),
        is_active=True,
        business_name="Private PDF Company",
        business_address="Private address",
        business_phone="+8801800000000",
        currency_code="BDT",
        timezone="Asia/Dhaka",
    )
    db_session.add(other_user)
    db_session.commit()
    other_token, _ = create_access_token(other_user.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    foreign = client.get(f"/api/v1/quotations/{quote['id']}/pdf", headers=other_headers)
    anonymous = client.get(f"/api/v1/quotations/{quote['id']}/pdf")
    assert foreign.status_code == 404
    assert anonymous.status_code == 401
