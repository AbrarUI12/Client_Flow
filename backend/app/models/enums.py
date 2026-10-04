from enum import StrEnum


class LeadStatus(StrEnum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    QUOTED = "QUOTED"
    WON = "WON"
    LOST = "LOST"


class LeadSource(StrEnum):
    WEBSITE = "WEBSITE"
    REFERRAL = "REFERRAL"
    LINKEDIN = "LINKEDIN"
    UPWORK = "UPWORK"
    FIVERR = "FIVERR"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    OTHER = "OTHER"


class QuotationStatus(StrEnum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
