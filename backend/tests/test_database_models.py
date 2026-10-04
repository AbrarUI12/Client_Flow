from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import Settings
from app.db.base import Base
from app.models.quotation import Quotation, QuotationItem, quotation_number_sequence
from app.models.user import User
from app.scripts.seed_demo_user import create_demo_user


def test_metadata_contains_complete_schema() -> None:
    assert set(Base.metadata.tables) == {
        "users",
        "leads",
        "quotations",
        "quotation_items",
        "follow_ups",
    }
    assert quotation_number_sequence.name == "quotation_number_seq"

    quotation_constraint_names = {constraint.name for constraint in Quotation.__table__.constraints}
    assert "uq_quotations_quote_number" in quotation_constraint_names
    assert "ck_quotations_valid_date_range" in quotation_constraint_names

    item_foreign_key = next(iter(QuotationItem.__table__.foreign_keys))
    assert item_foreign_key.ondelete == "CASCADE"


def test_demo_user_seed_is_idempotent() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    settings = Settings(_env_file=None)

    with Session(engine) as session:
        first_user, first_created = create_demo_user(session, settings)
        second_user, second_created = create_demo_user(session, settings)
        users = session.scalars(select(User)).all()

    assert first_created is True
    assert second_created is False
    assert first_user.id == second_user.id
    assert len(users) == 1
    assert users[0].email == "demo@clientflow.app"
    assert users[0].password_hash.startswith("$argon2")
