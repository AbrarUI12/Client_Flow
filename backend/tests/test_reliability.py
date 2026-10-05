from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from itertools import product
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import Engine, delete, func, inspect, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

import app.scripts.seed_demo_user as seed_module
import app.services.quotation_service as quotation_service
from alembic import command
from app.core.config import Settings
from app.db.base import Base
from app.main import app
from app.models.enums import LeadStatus, QuotationStatus
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.quotation import Quotation, QuotationItem
from app.models.user import User
from app.scripts.seed_demo_user import create_demo_user, seed_demo_data
from app.services.followup_service import require_owned_followup
from app.services.quotation_service import require_owned_quotation, transition_quotation_status

DEMO_EMAIL = "demo@clientflow.app"
DEMO_PASSWORD = "development-only-change-me"
BACKEND_ROOT = Path(__file__).resolve().parents[1]
STATUSES = ("DRAFT", "SENT", "ACCEPTED", "REJECTED")
LEGAL_TRANSITIONS = {("DRAFT", "SENT"), ("SENT", "ACCEPTED"), ("SENT", "REJECTED")}
FIXED_NOW = datetime(2026, 10, 5, 6, 0, tzinfo=UTC)


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_lead(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        "/api/v1/leads",
        headers=headers,
        json={"contact_name": "Reliability Client", "status": "QUALIFIED"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def quotation_payload(description: str = "Original item") -> dict:
    return {
        "issue_date": date.today().isoformat(),
        "valid_until": (date.today() + timedelta(days=14)).isoformat(),
        "items": [{"description": description, "quantity": "2.000", "unit_price": "50.00"}],
    }


def create_quote(client: TestClient, headers: dict[str, str], lead_id: str) -> dict:
    response = client.post(
        f"/api/v1/leads/{lead_id}/quotations",
        headers=headers,
        json=quotation_payload(),
    )
    assert response.status_code == 201, response.text
    return response.json()


def set_status(client: TestClient, headers: dict[str, str], quote_id: str, status: str):
    return client.patch(
        f"/api/v1/quotations/{quote_id}/status",
        headers=headers,
        json={"status": status},
    )


def quote_in_status(client: TestClient, headers: dict[str, str], status: str) -> dict:
    quote = create_quote(client, headers, create_lead(client, headers)["id"])
    path = {"DRAFT": [], "SENT": ["SENT"], "ACCEPTED": ["SENT", "ACCEPTED"]}
    for step in path.get(status, ["SENT", "REJECTED"]):
        response = set_status(client, headers, quote["id"], step)
        assert response.status_code == 200, response.text
        quote = response.json()
    return quote


def test_failed_multi_record_writes_leave_no_partial_state(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    draft = create_quote(client, headers, lead["id"])
    sent = quote_in_status(client, headers, "SENT")
    original_reload = quotation_service.require_owned_quotation
    failing = {"active": False}

    def reload_or_fail(*args: object, **kwargs: object) -> Quotation:
        # The services reload the record after flushing every write, so failing here proves
        # that already-flushed rows are rolled back with the request.
        if failing["active"]:
            raise RuntimeError("simulated failure after flush")
        return original_reload(*args, **kwargs)

    monkeypatch.setattr(quotation_service, "require_owned_quotation", reload_or_fail)
    failing["active"] = True
    with TestClient(app, raise_server_exceptions=False) as quiet_client:
        create = quiet_client.post(
            f"/api/v1/leads/{lead['id']}/quotations",
            headers=headers,
            json=quotation_payload("Should not persist"),
        )
        replace_items = quiet_client.patch(
            f"/api/v1/quotations/{draft['id']}",
            headers=headers,
            json={"items": [{"description": "Replacement", "quantity": "9", "unit_price": "9"}]},
        )
        accept = set_status(quiet_client, headers, sent["id"], "ACCEPTED")
    failing["active"] = False

    assert create.status_code == replace_items.status_code == accept.status_code == 500
    lead_quotes = client.get(f"/api/v1/leads/{lead['id']}/quotations", headers=headers).json()
    assert [quote["id"] for quote in lead_quotes["items"]] == [draft["id"]]
    orphan_items = db_session.scalar(
        select(func.count())
        .select_from(QuotationItem)
        .where(QuotationItem.description == "Should not persist")
    )
    assert orphan_items == 0
    unchanged_draft = client.get(f"/api/v1/quotations/{draft['id']}", headers=headers).json()
    assert [item["description"] for item in unchanged_draft["items"]] == ["Original item"]
    assert unchanged_draft["total"] == draft["total"]
    unchanged_sent = client.get(f"/api/v1/quotations/{sent['id']}", headers=headers).json()
    sent_lead = client.get(f"/api/v1/leads/{sent['lead_id']}", headers=headers).json()
    assert (unchanged_sent["status"], unchanged_sent["accepted_at"]) == ("SENT", None)
    assert sent_lead["status"] == "QUOTED"


def test_missing_records_return_stable_structured_404s(client: TestClient) -> None:
    headers = auth_headers(client)
    expectations = {
        f"/api/v1/leads/{uuid4()}": ("LEAD_NOT_FOUND", "The requested lead was not found."),
        f"/api/v1/quotations/{uuid4()}": (
            "QUOTATION_NOT_FOUND",
            "The requested quotation was not found.",
        ),
    }
    for url, (code, message) in expectations.items():
        response = client.get(url, headers=headers)
        assert response.status_code == 404
        assert response.json() == {"detail": {"code": code, "message": message}}

    followup = client.patch(f"/api/v1/follow-ups/{uuid4()}/complete", headers=headers)
    assert followup.status_code == 404
    assert followup.json() == {
        "detail": {
            "code": "FOLLOW_UP_NOT_FOUND",
            "message": "The requested follow-up was not found.",
        }
    }


@pytest.mark.parametrize(
    ("current", "target"),
    [pair for pair in product(STATUSES, STATUSES) if pair not in LEGAL_TRANSITIONS],
)
def test_every_illegal_transition_returns_a_stable_conflict(
    client: TestClient, current: str, target: str
) -> None:
    headers = auth_headers(client)
    quote = quote_in_status(client, headers, current)

    response = set_status(client, headers, quote["id"], target)
    after = client.get(f"/api/v1/quotations/{quote['id']}", headers=headers).json()

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "INVALID_QUOTATION_STATUS_TRANSITION"
    assert after["status"] == current
    assert after["updated_at"] == quote["updated_at"]


@pytest.mark.parametrize("status", ["SENT", "ACCEPTED", "REJECTED"])
def test_only_drafts_can_be_edited(client: TestClient, status: str) -> None:
    headers = auth_headers(client)
    quote = quote_in_status(client, headers, status)

    response = client.patch(
        f"/api/v1/quotations/{quote['id']}",
        headers=headers,
        json={"notes": "Late change"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "QUOTATION_NOT_EDITABLE"


def test_repeated_submissions_do_not_repeat_side_effects(client: TestClient) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    quote = create_quote(client, headers, lead["id"])
    first_send = set_status(client, headers, quote["id"], "SENT")
    second_send = set_status(client, headers, quote["id"], "SENT")
    first_accept = set_status(client, headers, quote["id"], "ACCEPTED")
    second_accept = set_status(client, headers, quote["id"], "ACCEPTED")
    first_archive = client.post(f"/api/v1/leads/{lead['id']}/archive", headers=headers)
    second_archive = client.post(f"/api/v1/leads/{lead['id']}/archive", headers=headers)

    assert first_send.status_code == first_accept.status_code == first_archive.status_code == 200
    assert second_send.status_code == second_accept.status_code == 409
    assert second_archive.status_code == 404
    sent_at = datetime.fromisoformat(first_send.json()["sent_at"])
    assert datetime.fromisoformat(first_accept.json()["sent_at"]) == sent_at
    assert client.get("/api/v1/leads", headers=headers).json()["total"] == 0


def test_mutations_lock_rows_so_concurrent_transitions_serialize(
    database_engine: Engine,
) -> None:
    owner_id, lead_id, quote_id, followup_id = uuid4(), uuid4(), uuid4(), uuid4()
    with Session(database_engine) as setup:
        setup.add(
            User(
                id=owner_id,
                email=f"lock-{owner_id}@example.com",
                full_name="Lock Owner",
                password_hash="not-used",
                business_name="Lock Studio",
                business_address="Lock address",
                business_phone="+8801700000000",
                currency_code="BDT",
                timezone="Asia/Dhaka",
            )
        )
        setup.flush()
        setup.add(Lead(id=lead_id, owner_id=owner_id, contact_name="Lock Lead"))
        setup.flush()
        setup.add_all(
            [
                Quotation(
                    id=quote_id,
                    lead_id=lead_id,
                    quote_number=f"Q-LOCK-{str(quote_id)[:8]}",
                    status=QuotationStatus.SENT,
                    valid_until=date.today() + timedelta(days=7),
                ),
                FollowUp(id=followup_id, lead_id=lead_id, note="Lock", due_at=FIXED_NOW),
            ]
        )
        setup.commit()

    try:
        with Session(database_engine) as first, Session(database_engine) as second:
            locked = require_owned_quotation(first, owner_id, quote_id, for_update=True)
            require_owned_followup(first, owner_id, followup_id, for_update=True)

            second.execute(text("SET LOCAL lock_timeout = '200ms'"))
            with pytest.raises(OperationalError):
                require_owned_quotation(second, owner_id, quote_id, for_update=True)
            second.rollback()
            second.execute(text("SET LOCAL lock_timeout = '200ms'"))
            with pytest.raises(OperationalError):
                require_owned_followup(second, owner_id, followup_id, for_update=True)
            second.rollback()

            transition_quotation_status(first, locked, QuotationStatus.ACCEPTED)
            first.commit()

            # The next writer re-reads the committed state and gets a clean business error.
            relocked = require_owned_quotation(second, owner_id, quote_id, for_update=True)
            assert relocked.status == QuotationStatus.ACCEPTED
            with pytest.raises(HTTPException) as conflict:
                transition_quotation_status(second, relocked, QuotationStatus.REJECTED)
            assert conflict.value.status_code == 409
            second.rollback()
    finally:
        with Session(database_engine) as cleanup:
            cleanup.execute(delete(FollowUp).where(FollowUp.id == followup_id))
            cleanup.execute(delete(Quotation).where(Quotation.id == quote_id))
            cleanup.execute(delete(Lead).where(Lead.id == lead_id))
            cleanup.execute(delete(User).where(User.id == owner_id))
            cleanup.commit()


def test_migrations_round_trip_on_an_empty_schema_and_match_the_models(
    database_engine: Engine,
) -> None:
    with database_engine.connect() as connection:
        transaction = connection.begin()
        try:
            config = Config()
            config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
            config.attributes["connection"] = connection

            command.downgrade(config, "base")
            assert set(inspect(connection).get_table_names()) == {"alembic_version"}
            assert connection.scalar(
                text("SELECT count(*) FROM pg_class WHERE relname = 'quotation_number_seq'")
            ) == 0

            command.upgrade(config, "head")
            context = MigrationContext.configure(
                connection,
                opts={"compare_type": True, "compare_server_default": True},
            )
            assert compare_metadata(context, Base.metadata) == []
            assert context.get_current_revision() == "20261005_0001"
        finally:
            transaction.rollback()


def test_seed_reset_is_atomic_when_recreation_fails(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(_env_file=None)
    seeded = seed_demo_data(db_session, settings, now=FIXED_NOW)

    def count_leads() -> int:
        return db_session.scalar(
            select(func.count()).select_from(Lead).where(Lead.owner_id == seeded.user.id)
        ) or 0

    before = count_leads()

    def fail_after_reset(*_: object, **__: object) -> None:
        raise RuntimeError("simulated failure while recreating demo data")

    monkeypatch.setattr(seed_module, "_create_demo_dataset", fail_after_reset)
    with pytest.raises(RuntimeError, match="simulated failure"):
        seed_demo_data(db_session, settings, reset=True, now=FIXED_NOW)

    assert before == 30
    assert count_leads() == before


def test_seed_refuses_unsafe_production_password_and_a_dataset_owned_by_another_account(
    db_session: Session,
) -> None:
    seed_demo_data(db_session, Settings(_env_file=None), now=FIXED_NOW)
    production = Settings(
        _env_file=None,
        environment="production",
        secret_key="a-private-production-signing-key-for-tests",
        database_url="postgresql+psycopg://clientflow@db.example.com/clientflow",
        cors_origins="https://clientflow.example.com",
        demo_user_email="production-demo@clientflow.app",
    )
    renamed = Settings(_env_file=None, demo_user_email="renamed-demo@clientflow.app")

    with pytest.raises(RuntimeError, match="DEMO_USER_PASSWORD"):
        create_demo_user(db_session, production)
    assert db_session.scalar(
        select(User).where(User.email == "production-demo@clientflow.app")
    ) is None

    for reset in (False, True):
        with pytest.raises(RuntimeError, match="different account"):
            seed_demo_data(db_session, renamed, reset=reset, now=FIXED_NOW)
    renamed_user = db_session.scalar(
        select(User).where(User.email == "renamed-demo@clientflow.app")
    )
    assert renamed_user is not None
    assert db_session.scalar(
        select(func.count()).select_from(Lead).where(Lead.owner_id == renamed_user.id)
    ) == 0


def test_won_and_lost_leads_keep_their_status_when_a_quote_is_sent(
    client: TestClient, db_session: Session
) -> None:
    headers = auth_headers(client)
    lead = create_lead(client, headers)
    quote = create_quote(client, headers, lead["id"])
    saved_lead = db_session.get(Lead, lead["id"])
    assert saved_lead is not None
    saved_lead.status = LeadStatus.LOST
    saved_lead.estimated_value = Decimal("1.00")
    db_session.commit()

    assert set_status(client, headers, quote["id"], "SENT").status_code == 200
    assert client.get(f"/api/v1/leads/{lead['id']}", headers=headers).json()["status"] == "LOST"
