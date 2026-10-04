from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def create_demo_user(session: Session, settings: Settings) -> tuple[User, bool]:
    email = settings.demo_user_email.strip().lower()
    existing_user = session.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        return existing_user, False

    password = settings.demo_user_password.get_secret_value()
    if settings.environment == "production" and password == "development-only-change-me":
        raise RuntimeError("Set DEMO_USER_PASSWORD before seeding a production environment.")

    user = User(
        email=email,
        full_name=settings.demo_user_full_name,
        password_hash=hash_password(password),
        is_active=True,
        business_name=settings.demo_business_name,
        business_address=settings.demo_business_address,
        business_phone=settings.demo_business_phone,
        currency_code=settings.demo_currency_code,
        timezone=settings.demo_timezone,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user, True


def main() -> None:
    settings = get_settings()
    with SessionLocal() as session:
        user, created = create_demo_user(session, settings)

    action = "Created" if created else "Already exists"
    print(f"{action}: demo user {user.email}")


if __name__ == "__main__":
    main()
