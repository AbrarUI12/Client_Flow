import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from alembic import command
from app.core.config import Settings
from app.dependencies.database import get_db
from app.main import app
from app.scripts.seed_demo_user import create_demo_user

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg://clientflow:clientflow@localhost:5432/clientflow_test"
)


def resolve_test_database_url() -> URL:
    url = make_url(os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL))
    if url.get_backend_name() != "postgresql":
        raise pytest.UsageError("TEST_DATABASE_URL must point to a PostgreSQL database.")
    if not (url.database or "").endswith("_test"):
        # The suite rebuilds the schema, so refuse anything that looks like a real database.
        raise pytest.UsageError("TEST_DATABASE_URL must name a database ending in '_test'.")
    return url


def alembic_config(connection: Connection) -> Config:
    config = Config()
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.attributes["connection"] = connection
    return config


def ensure_database_exists(url: URL) -> None:
    maintenance_engine = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    try:
        with maintenance_engine.connect() as connection:
            exists = connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            )
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        maintenance_engine.dispose()


@pytest.fixture(scope="session")
def database_engine() -> Generator[Engine, None, None]:
    url = resolve_test_database_url()
    try:
        ensure_database_exists(url)
    except OperationalError as error:
        pytest.exit(
            "PostgreSQL is required for the backend tests. Start it and set TEST_DATABASE_URL "
            f"(tried {url.render_as_string(hide_password=True)}): {error}",
            returncode=1,
        )

    engine = create_engine(url)
    # Every run proves the migrations build the complete schema from an empty database.
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        command.upgrade(alembic_config(connection), "head")

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(database_engine: Engine) -> Generator[Session, None, None]:
    # Each test runs inside one outer transaction that is always rolled back. Commits made by
    # application code only release savepoints, so tests never leak data into each other.
    connection = database_engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        create_demo_user(session, Settings(_env_file=None))
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
