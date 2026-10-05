import base64
import json
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from argon2 import Type, extract_parameters
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.api.v1.dashboard as dashboard_routes
import app.core.security as security
from app.api.v1 import auth, dashboard, followups, health, leads, quotations
from app.core.config import Settings, get_settings
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.main import app
from app.models.user import User

DEMO_EMAIL = "demo@clientflow.app"
DEMO_PASSWORD = "development-only-change-me"
PUBLIC_ROUTES = {("GET", "/api/v1/health"), ("POST", "/api/v1/auth/login")}
FEATURE_ROUTERS = (
    auth.router,
    dashboard.router,
    followups.router,
    health.router,
    leads.router,
    quotations.router,
)


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def api_routes() -> list[tuple[str, str, APIRoute]]:
    prefix = get_settings().api_v1_prefix
    return [
        (method, f"{prefix}{route.path}", route)
        for router in FEATURE_ROUTERS
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in sorted(route.methods)
    ]


def openapi_operations() -> dict[tuple[str, str], dict[str, object]]:
    return {
        (method.upper(), path): operation
        for path, path_item in app.openapi()["paths"].items()
        for method, operation in path_item.items()
    }


def protected_routes() -> list[tuple[str, str]]:
    return sorted(set(openapi_operations()) - PUBLIC_ROUTES)


def concrete_path(path: str) -> str:
    for name in ("lead_id", "quotation_id", "followup_id"):
        path = path.replace(f"{{{name}}}", str(uuid4()))
    return path


def dependency_tree(dependant: Dependant) -> list[Dependant]:
    nodes = [dependant]
    for child in dependant.dependencies:
        nodes.extend(dependency_tree(child))
    return nodes


def signed_token(payload: dict[str, object], key: str | None = None) -> str:
    settings = get_settings()
    return jwt.encode(
        payload,
        key or settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def unsigned_token(payload: dict[str, object]) -> str:
    def segment(value: dict[str, object]) -> str:
        raw = json.dumps(value, default=str).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    return f"{segment({'alg': 'none', 'typ': 'JWT'})}.{segment(payload)}."


def demo_user(db_session: Session) -> User:
    user = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))
    assert user is not None
    return user


def test_route_inventory_is_complete_and_only_health_and_login_are_public() -> None:
    operations = openapi_operations()
    routes = {(method, path) for method, path, _ in api_routes()}

    # The feature routers checked below are exactly the operations the application serves.
    assert routes == set(operations)
    assert PUBLIC_ROUTES <= routes
    assert len(protected_routes()) == 20
    for method, path, route in api_routes():
        calls = {node.call for node in dependency_tree(route.dependant)}
        declares_bearer = operations[(method, path)].get("security") == [{"HTTPBearer": []}]
        if (method, path) in PUBLIC_ROUTES:
            assert get_current_user not in calls, f"{method} {path} must stay public"
            assert not declares_bearer
        else:
            assert get_current_user in calls, f"{method} {path} must require authentication"
            assert declares_bearer


@pytest.mark.parametrize(("method", "path"), protected_routes())
def test_every_protected_route_rejects_missing_and_invalid_tokens(
    client: TestClient, method: str, path: str
) -> None:
    url = concrete_path(path)
    body = {} if method in {"POST", "PATCH"} else None

    anonymous = client.request(method, url, json=body)
    malformed = client.request(
        method,
        url,
        json=body,
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert anonymous.status_code == 401
    assert anonymous.json()["detail"]["code"] == "AUTHENTICATION_REQUIRED"
    assert anonymous.headers["www-authenticate"] == "Bearer"
    assert malformed.status_code == 401
    assert malformed.json()["detail"]["code"] == "INVALID_TOKEN"


def test_forged_incomplete_and_foreign_tokens_are_rejected(
    client: TestClient, db_session: Session
) -> None:
    user = demo_user(db_session)
    now = datetime.now(UTC)
    valid_claims = {
        "sub": str(user.id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }

    def without(claim: str) -> dict[str, object]:
        return {key: value for key, value in valid_claims.items() if key != claim}

    rejected_tokens = {
        "alg none": unsigned_token(valid_claims),
        "foreign key": signed_token(valid_claims, key="another-signing-key-of-32-bytes-or-more"),
        "wrong type": signed_token({**valid_claims, "type": "refresh"}),
        "missing type": signed_token(without("type")),
        "missing subject": signed_token(without("sub")),
        "non-uuid subject": signed_token({**valid_claims, "sub": "demo@clientflow.app"}),
        "missing expiry": signed_token(without("exp")),
        "missing issued-at": signed_token(without("iat")),
        "expired": signed_token({**valid_claims, "exp": now - timedelta(seconds=1)}),
        "unknown user": signed_token({**valid_claims, "sub": str(uuid4())}),
    }

    assert client.get(
        "/api/v1/leads",
        headers={"Authorization": f"Bearer {signed_token(valid_claims)}"},
    ).status_code == 200
    for label, token in rejected_tokens.items():
        response = client.get("/api/v1/leads", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401, label
        assert response.json()["detail"]["code"] == "INVALID_TOKEN", label

    for header in ("Basic ZGVtbzpwYXNzd29yZA==", "Bearer", "Bearer "):
        response = client.get("/api/v1/leads", headers={"Authorization": header})
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "AUTHENTICATION_REQUIRED"


def test_inactive_user_token_is_rejected(client: TestClient, db_session: Session) -> None:
    headers = auth_headers(client)
    demo_user(db_session).is_active = False
    db_session.commit()

    response = client.get("/api/v1/leads", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "ACCOUNT_INACTIVE"


def test_login_failures_are_indistinguishable_and_always_verify_a_hash(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    verified_hashes: list[str] = []
    original_verify = security.verify_password

    def recording_verify(password: str, password_hash: str) -> bool:
        verified_hashes.append(password_hash)
        return original_verify(password, password_hash)

    monkeypatch.setattr(security, "verify_password", recording_verify)

    unknown = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@clientflow.app", "password": DEMO_PASSWORD},
    )
    wrong = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": "wrong-password"},
    )
    demo_user(db_session).is_active = False
    db_session.commit()
    inactive = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )

    responses = (unknown, wrong, inactive)
    assert {response.status_code for response in responses} == {401}
    assert unknown.json() == wrong.json() == inactive.json()
    assert {response.headers["www-authenticate"] for response in responses} == {"Bearer"}
    # Unknown accounts are still checked against a real Argon2 hash to equalize timing.
    assert verified_hashes[0] == security.dummy_password_hash
    assert len(verified_hashes) == 3


def test_login_validation_errors_do_not_depend_on_account_existence(client: TestClient) -> None:
    registered = client.post("/api/v1/auth/login", json={"email": DEMO_EMAIL, "password": ""})
    unregistered = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@clientflow.app", "password": ""},
    )

    assert registered.status_code == unregistered.status_code == 422
    assert [error["type"] for error in registered.json()["detail"]] == [
        error["type"] for error in unregistered.json()["detail"]
    ]


def test_passwords_are_stored_as_argon2id_and_never_returned(
    client: TestClient, db_session: Session
) -> None:
    parameters = extract_parameters(demo_user(db_session).password_hash)
    headers = auth_headers(client)
    me = client.get("/api/v1/auth/me", headers=headers)

    assert parameters.type is Type.ID
    assert parameters.memory_cost >= 19 * 1024
    assert parameters.time_cost >= 2
    assert DEMO_PASSWORD not in me.text
    assert "password" not in me.text


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"secret_key": "development-only-change-me-at-least-32-bytes"}, "SECRET_KEY"),
        ({"secret_key": "replace-with-a-long-random-secret"}, "SECRET_KEY"),
        ({"secret_key": "too-short"}, "SECRET_KEY"),
        ({"database_url": "postgresql+psycopg://clientflow:clientflow@localhost:5432/clientflow"},
         "DATABASE_URL"),
        ({"cors_origins": "*"}, "CORS_ORIGINS"),
        ({"cors_origins": "https://clientflow.example.com,*"}, "CORS_ORIGINS"),
        ({"cors_origins": " , "}, "CORS_ORIGINS"),
    ],
)
def test_production_settings_refuse_public_or_unsafe_values(
    overrides: dict[str, str], message: str
) -> None:
    production = {
        "environment": "production",
        "secret_key": "a-private-production-signing-key-for-tests",
        "database_url": "postgresql+psycopg://clientflow@db.example.com/clientflow",
        "cors_origins": "https://clientflow.example.com",
    }

    assert Settings(_env_file=None, **production).environment == "production"
    with pytest.raises(ValidationError, match=message):
        Settings(_env_file=None, **{**production, **overrides})


def test_development_defaults_remain_usable_outside_production() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.cors_origin_list == ["http://localhost:5173"]


def test_cors_allows_only_the_configured_origin_and_needed_request_shape(
    client: TestClient,
) -> None:
    allowed = client.options(
        "/api/v1/leads",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    foreign_preflight = client.options(
        "/api/v1/leads",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    unneeded_method = client.options(
        "/api/v1/leads",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "DELETE",
        },
    )
    foreign_simple = client.get("/api/v1/health", headers={"Origin": "https://evil.example"})
    download = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in allowed.headers
    assert foreign_preflight.status_code == 400
    assert "access-control-allow-origin" not in foreign_preflight.headers
    assert unneeded_method.status_code == 400
    assert "access-control-allow-origin" not in foreign_simple.headers
    assert download.headers["access-control-expose-headers"] == "Content-Disposition"


def test_unhandled_errors_do_not_expose_internals(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(*_: object, **__: object) -> None:
        raise RuntimeError("database password=hunter2 at internal-host")

    monkeypatch.setattr(dashboard_routes, "build_dashboard_summary", explode)
    headers = auth_headers(client)
    with TestClient(app, raise_server_exceptions=False) as quiet_client:
        response = quiet_client.get("/api/v1/dashboard/summary", headers=headers)

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert "hunter2" not in response.text
    assert "Traceback" not in response.text


def test_every_route_shares_one_function_scoped_database_session() -> None:
    for method, path, route in api_routes():
        database_dependencies = [
            node for node in dependency_tree(route.dependant) if node.call is get_db
        ]
        for node in database_dependencies:
            assert node.scope == "function", f"{method} {path} must commit before responding"


def test_a_failed_commit_is_reported_instead_of_a_success_response(
    client: TestClient, db_session: Session
) -> None:
    headers = auth_headers(client)
    sessions_opened: list[Session] = []

    def failing_commit() -> Generator[Session, None, None]:
        sessions_opened.append(db_session)
        yield db_session
        db_session.rollback()
        raise RuntimeError("simulated commit failure")

    app.dependency_overrides[get_db] = failing_commit
    with TestClient(app, raise_server_exceptions=False) as quiet_client:
        response = quiet_client.post(
            "/api/v1/leads",
            headers=headers,
            json={"contact_name": "Never committed"},
        )

    assert response.status_code == 500
    # The route and the authentication dependency share one session per request.
    assert len(sessions_opened) == 1
