from sqlalchemy import select
from sqlalchemy.orm import Session

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


def test_demo_user_seed_is_idempotent(db_session: Session) -> None:
    settings = Settings(_env_file=None, demo_user_email="seed-check@clientflow.app")

    first_user, first_created = create_demo_user(db_session, settings)
    second_user, second_created = create_demo_user(db_session, settings)
    users = db_session.scalars(
        select(User).where(User.email == "seed-check@clientflow.app")
    ).all()

    assert first_created is True
    assert second_created is False
    assert first_user.id == second_user.id
    assert len(users) == 1
    assert users[0].password_hash.startswith("$argon2")
