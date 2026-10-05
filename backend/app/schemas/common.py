from pydantic import BaseModel, field_validator


def ensure_storable_text(value: str) -> str:
    """Reject NUL characters, which PostgreSQL text columns cannot store, before any SQL runs."""
    if "\x00" in value:
        raise ValueError("Text cannot contain NUL characters")
    return value


class RequestModel(BaseModel):
    """Base class for request bodies; applies storable-text validation to every string field."""

    @field_validator("*", mode="after")
    @classmethod
    def reject_unstorable_text(cls, value: object) -> object:
        if isinstance(value, str):
            ensure_storable_text(value)
        return value
