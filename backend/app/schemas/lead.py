from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.enums import LeadSource, LeadStatus
from app.schemas.common import RequestModel


class LeadFields(RequestModel):
    contact_name: str = Field(min_length=1, max_length=100)
    company: str | None = Field(default=None, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    source: LeadSource | None = None
    status: LeadStatus = LeadStatus.NEW
    estimated_value: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=14, decimal_places=2)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("contact_name")
    @classmethod
    def normalize_contact_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Contact name is required")
        return normalized

    @field_validator("company", "phone", "notes", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_optional_email(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized or None
        return value


class LeadCreate(LeadFields):
    pass


class LeadUpdate(RequestModel):
    contact_name: str | None = Field(default=None, min_length=1, max_length=100)
    company: str | None = Field(default=None, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    source: LeadSource | None = None
    status: LeadStatus | None = None
    estimated_value: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("contact_name")
    @classmethod
    def normalize_optional_contact_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Contact name cannot be blank")
        return normalized

    @field_validator("company", "phone", "notes", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_optional_email(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized or None
        return value

    @model_validator(mode="after")
    def prevent_null_required_fields(self) -> "LeadUpdate":
        for field_name in ("contact_name", "status", "estimated_value"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contact_name: str
    company: str | None
    email: EmailStr | None
    phone: str | None
    source: LeadSource | None
    status: LeadStatus
    estimated_value: Decimal
    notes: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class LeadListResponse(BaseModel):
    items: list[LeadResponse]
    page: int
    page_size: int
    total: int
    pages: int
