from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User

DEMO_EMAIL = "demo@clientflow.app"
DEMO_PASSWORD = "development-only-change-me"


def login(client: TestClient, password: str = DEMO_PASSWORD) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def test_correct_password_logs_in_and_hash_is_valid(
    client: TestClient, db_session: Session
) -> None:
    payload = login(client)
    user = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))

    assert payload["token_type"] == "bearer"
    assert isinstance(payload["access_token"], str)
    assert payload["expires_in"] == 3600
    assert user is not None
    assert user.password_hash != DEMO_PASSWORD
    assert verify_password(DEMO_PASSWORD, user.password_hash)


def test_wrong_password_and_unknown_user_return_same_safe_error(client: TestClient) -> None:
    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": "definitely-wrong"},
    )
    unknown_user = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "definitely-wrong"},
    )

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert (
        wrong_password.json()
        == unknown_user.json()
        == {
            "detail": {
                "code": "INVALID_CREDENTIALS",
                "message": "The email or password is incorrect.",
            }
        }
    )


def test_inactive_user_cannot_log_in(client: TestClient, db_session: Session) -> None:
    user = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))
    assert user is not None
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_anonymous_access_to_me_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTHENTICATION_REQUIRED"


def test_valid_token_returns_current_user_without_password_hash(client: TestClient) -> None:
    token = login(client)["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == DEMO_EMAIL
    assert payload["business_name"] == "ClientFlow Demo Company"
    assert "password" not in payload
    assert "password_hash" not in payload


def test_invalid_and_expired_tokens_are_rejected(client: TestClient, db_session: Session) -> None:
    user = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))
    assert user is not None
    expired_token, _ = create_access_token(user.id, expires_delta=timedelta(seconds=-1))

    invalid_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    expired_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert invalid_response.status_code == 401
    assert expired_response.status_code == 401
    assert invalid_response.json()["detail"]["code"] == "INVALID_TOKEN"
    assert expired_response.json()["detail"]["code"] == "INVALID_TOKEN"


def test_logout_is_an_authenticated_semantic_endpoint(client: TestClient) -> None:
    token = login(client)["access_token"]
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert response.content == b""
