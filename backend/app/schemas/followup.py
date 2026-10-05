from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FollowUpCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    due_at: datetime
    note: str = Field(min_length=1, max_length=5000)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Follow-up note is required")
        return normalized

    @field_validator("due_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("due_at must include a timezone offset")
        return value.astimezone(UTC)


class FollowUpUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    due_at: datetime | None = None
    note: str | None = Field(default=None, min_length=1, max_length=5000)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Follow-up note cannot be blank")
        return normalized

    @field_validator("due_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("due_at must include a timezone offset")
        return value.astimezone(UTC) if value is not None else None

    @model_validator(mode="after")
    def prevent_explicit_nulls(self) -> "FollowUpUpdate":
        for field_name in ("due_at", "note"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class FollowUpLeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contact_name: str
    company: str | None


class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    due_at: datetime
    note: str
    is_completed: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    lead: FollowUpLeadResponse


class FollowUpListResponse(BaseModel):
    items: list[FollowUpResponse]
    total: int
