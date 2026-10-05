from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import QuotationStatus
from app.schemas.common import RequestModel


class QuotationItemInput(RequestModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit_price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Item description is required")
        return normalized


class QuotationCreate(RequestModel):
    model_config = ConfigDict(extra="forbid")

    issue_date: date
    valid_until: date
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, decimal_places=2)
    tax_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, decimal_places=2)
    notes: str | None = Field(default=None, max_length=5000)
    items: list[QuotationItemInput] = Field(min_length=1, max_length=100)

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_notes(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @model_validator(mode="after")
    def validate_date_range(self) -> "QuotationCreate":
        if self.valid_until < self.issue_date:
            raise ValueError("valid_until must be on or after issue_date")
        return self


class QuotationUpdate(RequestModel):
    model_config = ConfigDict(extra="forbid")

    issue_date: date | None = None
    valid_until: date | None = None
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100, decimal_places=2)
    tax_percent: Decimal | None = Field(default=None, ge=0, le=100, decimal_places=2)
    notes: str | None = Field(default=None, max_length=5000)
    items: list[QuotationItemInput] | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_notes(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @model_validator(mode="after")
    def prevent_nulls_and_validate_dates(self) -> "QuotationUpdate":
        for field_name in ("issue_date", "valid_until", "discount_percent", "tax_percent", "items"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        if self.issue_date is not None and self.valid_until is not None:
            if self.valid_until < self.issue_date:
                raise ValueError("valid_until must be on or after issue_date")
        return self


class QuotationStatusUpdate(RequestModel):
    model_config = ConfigDict(extra="forbid")

    status: QuotationStatus


class QuotationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    sort_order: int


class QuotationLeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contact_name: str
    company: str | None
    email: str | None


class QuotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    quote_number: str
    status: QuotationStatus
    issue_date: date
    valid_until: date
    subtotal: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    tax_percent: Decimal
    tax_amount: Decimal
    total: Decimal
    notes: str | None
    sent_at: datetime | None
    accepted_at: datetime | None
    rejected_at: datetime | None
    created_at: datetime
    updated_at: datetime
    lead: QuotationLeadResponse
    items: list[QuotationItemResponse]


class QuotationListResponse(BaseModel):
    items: list[QuotationResponse]
    page: int
    page_size: int
    total: int
    pages: int
