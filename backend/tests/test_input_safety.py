import csv
import io
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.main import app
from app.models.lead import Lead
from app.models.user import User

DEMO_EMAIL = "demo@clientflow.app"
DEMO_PASSWORD = "development-only-change-me"
MALFORMED_IDS = ("not-a-uuid", "1 OR 1=1", "x" * 300, "%C3%A9t%C3%A9", "00000000-0000")


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_lead(client: TestClient, headers: dict[str, str], **overrides: object) -> dict:
    payload: dict[str, object] = {"contact_name": "Input Safety Client", "status": "QUALIFIED"}
    payload.update(overrides)
    response = client.post("/api/v1/leads", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def quotation_payload(**overrides: object) -> dict:
    payload: dict[str, object] = {
        "issue_date": date.today().isoformat(),
        "valid_until": (date.today() + timedelta(days=14)).isoformat(),
        "items": [{"description": "Service", "quantity": "1.000", "unit_price": "10.00"}],
    }
    payload.update(overrides)
    return payload


def create_quote(client: TestClient, headers: dict[str, str], lead_id: str, **overrides) -> dict:
    response = client.post(
        f"/api/v1/leads/{lead_id}/quotations",
        headers=headers,
        json=quotation_payload(**overrides),
    )
    assert response.status_code == 201, response.text
    return response.json()


def id_routes() -> list[tuple[str, str]]:
    return sorted(
        (method.upper(), path)
        for path, path_item in app.openapi()["paths"].items()
        for method in path_item
        if "_id}" in path
    )


@pytest.mark.parametrize(("method", "path"), id_routes())
def test_malformed_path_ids_are_rejected_before_any_query(
    client: TestClient, method: str, path: str
) -> None:
    headers = auth_headers(client)
    for malformed_id in MALFORMED_IDS:
        url = path.replace("{lead_id}", malformed_id)
        url = url.replace("{quotation_id}", malformed_id).replace("{followup_id}", malformed_id)
        body = {} if method in {"POST", "PATCH"} else None
        response = client.request(method, url, headers=headers, json=body)

        assert response.status_code in {404, 422}, (url, response.text)
        if response.status_code == 422:
            assert any(error["loc"][0] == "path" for error in response.json()["detail"])


def test_malformed_query_ids_and_unknown_filters_are_rejected(client: TestClient) -> None:
    headers = auth_headers(client)
    invalid_requests = [
        "/api/v1/follow-ups?lead_id=not-a-uuid",
        "/api/v1/follow-ups?group=someday",
        "/api/v1/leads?status=ARCHIVED",
        "/api/v1/leads?source=BILLBOARD",
        "/api/v1/quotations?status=PAID",
    ]
    lead = create_lead(client, headers)
    invalid_requests.append(f"/api/v1/leads/{lead['id']}/quotations?status=PAID")

    for url in invalid_requests:
        assert client.get(url, headers=headers).status_code == 422, url


@pytest.mark.parametrize("path", ["/api/v1/leads", "/api/v1/quotations"])
def test_pagination_and_search_bounds(client: TestClient, path: str) -> None:
    headers = auth_headers(client)
    rejected = [
        "page=0",
        "page=100001",
        "page=9223372036854775807",
        "page_size=0",
        "page_size=101",
        f"search={'x' * 101}",
    ]

    for query in rejected:
        assert client.get(f"{path}?{query}", headers=headers).status_code == 422, query
    last_page = client.get(f"{path}?page=100000&page_size=100", headers=headers)
    assert last_page.status_code == 200
    assert last_page.json()["items"] == []


def test_follow_up_limit_bounds(client: TestClient) -> None:
    headers = auth_headers(client)

    assert client.get("/api/v1/follow-ups?limit=0", headers=headers).status_code == 422
    assert client.get("/api/v1/follow-ups?limit=501", headers=headers).status_code == 422
    assert client.get("/api/v1/follow-ups?limit=500", headers=headers).status_code == 200


def test_search_treats_like_wildcards_literally(client: TestClient) -> None:
    headers = auth_headers(client)
    for name in ("100% Pure", "Under_score Co", "Back\\slash Ltd", "Plain Client"):
        create_lead(client, headers, contact_name=name)

    def names(search: str) -> set[str]:
        response = client.get("/api/v1/leads", headers=headers, params={"search": search})
        assert response.status_code == 200
        return {item["contact_name"] for item in response.json()["items"]}

    assert names("%") == {"100% Pure"}
    assert names("_") == {"Under_score Co"}
    assert names("\\") == {"Back\\slash Ltd"}


def test_text_postgresql_cannot_store_is_rejected_with_422(client: TestClient) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    quote = create_quote(client, headers, lead["id"])
    followup = client.post(
        f"/api/v1/leads/{lead['id']}/follow-ups",
        headers=headers,
        json={"note": "Call back", "due_at": "2026-10-06T10:00:00+06:00"},
    ).json()
    json_headers = {**headers, "Content-Type": "application/json"}
    item = '{"description": "Item%s", "quantity": "1", "unit_price": "1.00"}'
    dates = (
        f'"issue_date": "{date.today().isoformat()}", '
        f'"valid_until": "{date.today().isoformat()}"'
    )

    for unstorable in ("\\u0000", "\\ud800"):
        requests = [
            ("POST", "/api/v1/leads", f'{{"contact_name": "Name{unstorable}"}}'),
            ("POST", "/api/v1/leads", f'{{"contact_name": "Ok", "notes": "x{unstorable}"}}'),
            ("PATCH", f"/api/v1/leads/{lead['id']}", f'{{"company": "Co{unstorable}"}}'),
            (
                "POST",
                f"/api/v1/leads/{lead['id']}/quotations",
                f'{{{dates}, "items": [{item % unstorable}]}}',
            ),
            ("PATCH", f"/api/v1/quotations/{quote['id']}", f'{{"notes": "n{unstorable}"}}'),
            (
                "POST",
                f"/api/v1/leads/{lead['id']}/follow-ups",
                f'{{"note": "n{unstorable}", "due_at": "2026-10-06T10:00:00+06:00"}}',
            ),
            ("PATCH", f"/api/v1/follow-ups/{followup['id']}", f'{{"note": "n{unstorable}"}}'),
            (
                "POST",
                "/api/v1/auth/login",
                f'{{"email": "{DEMO_EMAIL}", "password": "p{unstorable}"}}',
            ),
        ]
        for method, url, body in requests:
            response = client.request(method, url, headers=json_headers, content=body)
            assert response.status_code == 422, (method, url, unstorable, response.text)

    for url in ("/api/v1/leads", "/api/v1/quotations"):
        response = client.get(url, headers=headers, params={"search": "a\x00b"})
        assert response.status_code == 422

    # Validation errors never echo submitted values such as passwords.
    login = client.post("/api/v1/auth/login", json={"email": "not-an-email", "password": "s3cr3t"})
    assert login.status_code == 422
    assert "s3cr3t" not in login.text
    assert all("input" not in error for error in login.json()["detail"])


def test_quotation_body_limits_and_client_controlled_fields(client: TestClient) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    one_item = {"description": "Service", "quantity": "1.000", "unit_price": "10.00"}
    invalid_payloads = {
        "too many items": quotation_payload(items=[one_item] * 101),
        "long description": quotation_payload(items=[{**one_item, "description": "x" * 501}]),
        "long notes": quotation_payload(notes="x" * 5001),
        "quantity precision": quotation_payload(items=[{**one_item, "quantity": "1.0001"}]),
        "price precision": quotation_payload(items=[{**one_item, "unit_price": "1.001"}]),
        "not a number": quotation_payload(items=[{**one_item, "unit_price": "NaN"}]),
        "infinite": quotation_payload(items=[{**one_item, "quantity": "Infinity"}]),
        "discount above 100": quotation_payload(discount_percent="100.01"),
        "client quote number": quotation_payload(quote_number="Q-2026-000001"),
        "client status": quotation_payload(status="ACCEPTED"),
        "client line total": quotation_payload(items=[{**one_item, "line_total": "1.00"}]),
    }

    for label, payload in invalid_payloads.items():
        response = client.post(
            f"/api/v1/leads/{lead['id']}/quotations",
            headers=headers,
            json=payload,
        )
        assert response.status_code == 422, label

    too_large = client.post(
        f"/api/v1/leads/{lead['id']}/quotations",
        headers=headers,
        json=quotation_payload(
            items=[{**one_item, "quantity": "999999999.999", "unit_price": "999999999999.99"}]
        ),
    )
    assert too_large.status_code == 422
    assert too_large.json()["detail"]["code"] == "QUOTATION_TOTAL_TOO_LARGE"

    quote = create_quote(client, headers, lead["id"])
    status_extra = client.patch(
        f"/api/v1/quotations/{quote['id']}/status",
        headers=headers,
        json={"status": "SENT", "accepted_at": "2026-01-01T00:00:00Z"},
    )
    partial_dates = client.patch(
        f"/api/v1/quotations/{quote['id']}",
        headers=headers,
        json={"valid_until": (date.today() - timedelta(days=1)).isoformat()},
    )
    assert status_extra.status_code == 422
    assert partial_dates.status_code == 422
    assert partial_dates.json()["detail"]["code"] == "INVALID_QUOTATION_DATE_RANGE"


def test_lead_limits_and_mass_assignment_are_safe(client: TestClient, db_session: Session) -> None:
    headers = auth_headers(client)
    invalid_payloads = [
        {"contact_name": "x" * 101},
        {"contact_name": "Valid", "company": "x" * 151},
        {"contact_name": "Valid", "phone": "1" * 51},
        {"contact_name": "Valid", "notes": "x" * 5001},
        {"contact_name": "Valid", "estimated_value": "1.001"},
        {"contact_name": "Valid", "estimated_value": "1000000000000.00"},
        {"contact_name": "Valid", "estimated_value": "NaN"},
    ]
    for payload in invalid_payloads:
        assert client.post("/api/v1/leads", headers=headers, json=payload).status_code == 422

    other_owner_id = "00000000-0000-0000-0000-000000000001"
    lead = create_lead(
        client,
        headers,
        id="00000000-0000-0000-0000-000000000002",
        owner_id=other_owner_id,
        is_archived=True,
    )
    saved = db_session.get(Lead, lead["id"])
    demo = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))
    assert demo is not None and saved is not None
    assert lead["id"] != "00000000-0000-0000-0000-000000000002"
    assert saved.owner_id == demo.id
    assert saved.is_archived is False


def test_follow_up_due_dates_outside_the_supported_range_are_rejected(client: TestClient) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)

    for due_at in ("0001-01-01T00:00:00+14:00", "9999-12-31T23:59:59-14:00"):
        response = client.post(
            f"/api/v1/leads/{lead['id']}/follow-ups",
            headers=headers,
            json={"note": "Edge of time", "due_at": due_at},
        )
        assert response.status_code == 422, due_at
    extra_field = client.post(
        f"/api/v1/leads/{lead['id']}/follow-ups",
        headers=headers,
        json={"note": "Extra", "due_at": "2026-10-06T10:00:00+06:00", "is_completed": True},
    )
    assert extra_field.status_code == 422


def test_csv_neutralizes_every_formula_prefix_in_every_text_column(
    client: TestClient, db_session: Session
) -> None:
    headers = auth_headers(client)
    for prefix in ("=", "+", "-", "@"):
        create_lead(
            client,
            headers,
            contact_name=f"{prefix}Name",
            company=f"{prefix}Company",
            email=f"{prefix}mail@example.com" if prefix != "@" else None,
            phone=f"{prefix}1700",
            notes=f"\n {prefix}notes",
        )
    demo = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))
    assert demo is not None
    # Stored data that bypasses API normalization is still neutralized on export.
    db_session.add(
        Lead(
            owner_id=demo.id,
            contact_name="\t=Tabbed",
            company="\r=Return",
            estimated_value=Decimal("0.00"),
        )
    )
    db_session.commit()

    response = client.get("/api/v1/leads/export", headers=headers)
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    text_columns = ("Contact Name", "Company", "Email", "Phone", "Notes")

    assert response.status_code == 200
    assert len(rows) == 5
    for row in rows:
        for column in text_columns:
            value = row[column]
            if value.lstrip()[:1] in {"=", "+", "-", "@"} or value[:1] in {"\t", "\r"}:
                pytest.fail(f"{column} was exported as a formula: {value!r}")


def test_pdf_renders_markup_literally_and_survives_line_breaks_in_single_line_fields(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    hostile = '<font color="red">Red</font> <a href="https://evil.example">click</a> <img src="x"/>'
    lead = create_lead(
        client,
        headers,
        contact_name="<b>Bold</b> & Co",
        company="a\n" * 74 + "a",
    )
    quote = create_quote(
        client,
        headers,
        lead["id"],
        notes=hostile,
        items=[
            {"description": hostile, "quantity": "1.000", "unit_price": "10.00"},
            {"description": "Tall\n" * 80 + "row", "quantity": "1.000", "unit_price": "5.00"},
        ],
    )

    response = client.get(f"/api/v1/quotations/{quote['id']}/pdf", headers=headers)
    reader = PdfReader(io.BytesIO(response.content))
    text = "\n".join(page.extract_text() for page in reader.pages)

    assert response.status_code == 200
    assert b"/URI" not in response.content
    assert '<font color="red">Red</font>' in text
    assert "<b>Bold</b> & Co" in text
    assert "Tall Tall Tall" in text
