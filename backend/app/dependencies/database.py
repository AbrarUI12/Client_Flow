from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Function scope makes the commit (or rollback) finish before the response is sent, so a client
# never receives a success response for work that failed to commit. Every route and the auth
# dependency share this one declaration, so a request uses a single session and transaction.
DbSession = Annotated[Session, Depends(get_db, scope="function")]
