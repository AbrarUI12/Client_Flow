import argparse
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid5
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import LeadSource, LeadStatus, QuotationStatus
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.quotation import Quotation, QuotationItem
from app.models.user import User
from app.schemas.quotation import QuotationItemInput
from app.services.quotation_service import calculate_quotation

DEMO_NAMESPACE = UUID("77251e48-9408-4c11-bc89-c158d5649a2f")
DEMO_QUOTE_NUMBER_START = 900001


@dataclass(frozen=True)
class DemoLead:
    key: str
    contact_name: str
    company: str
    source: LeadSource
    status: LeadStatus
    estimated_value: str
    notes: str


@dataclass(frozen=True)
class DemoQuote:
    key: str
    lead_key: str
    status: QuotationStatus
    days_ago: int
    discount_percent: str
    tax_percent: str
    notes: str
    items: tuple[tuple[str, str, str], ...]


@dataclass(frozen=True)
class DemoFollowUp:
    key: str
    lead_key: str
    day_offset: int
    hour: int
    note: str
    completed: bool = False


@dataclass(frozen=True)
class SeedResult:
    user: User
    user_created: bool
    dataset_created: bool
    reset: bool
    lead_count: int
    quotation_count: int
    item_count: int
    followup_count: int


DEMO_LEADS = (
    DemoLead(
        "naila-islam",
        "Naila Islam",
        "Bengal Loom",
        LeadSource.REFERRAL,
        LeadStatus.NEW,
        "85000.00",
        "Interested in an ecommerce discovery workshop.",
    ),
    DemoLead(
        "arif-hossain",
        "Arif Hossain",
        "Dhaka Roasters",
        LeadSource.WEBSITE,
        LeadStatus.CONTACTED,
        "120000.00",
        "Needs a refreshed brand site before the winter campaign.",
    ),
    DemoLead(
        "farhana-kabir",
        "Farhana Kabir",
        "Shobuj Health",
        LeadSource.LINKEDIN,
        LeadStatus.QUALIFIED,
        "240000.00",
        "Qualified for a patient portal design engagement.",
    ),
    DemoLead(
        "hasan-mahmud",
        "Hasan Mahmud",
        "Riverstone Labs",
        LeadSource.UPWORK,
        LeadStatus.QUOTED,
        "175000.00",
        "Proposal sent for a SaaS onboarding redesign.",
    ),
    DemoLead(
        "laila-chowdhury",
        "Laila Chowdhury",
        "Northstar Education",
        LeadSource.REFERRAL,
        LeadStatus.WON,
        "310000.00",
        "Accepted the learning platform product design proposal.",
    ),
    DemoLead(
        "tahmid-rahman",
        "Tahmid Rahman",
        "Copper & Clay",
        LeadSource.EMAIL,
        LeadStatus.LOST,
        "95000.00",
        "Chose an internal team after proposal review.",
    ),
    DemoLead(
        "samira-akter",
        "Samira Akter",
        "Meghna Foods",
        LeadSource.FIVERR,
        LeadStatus.NEW,
        "65000.00",
        "Requested an initial packaging website consultation.",
    ),
    DemoLead(
        "rakib-sarker",
        "Rakib Sarker",
        "Orbit Logistics",
        LeadSource.PHONE,
        LeadStatus.CONTACTED,
        "140000.00",
        "Follow up after operations stakeholder meeting.",
    ),
    DemoLead(
        "zara-ahmed",
        "Zara Ahmed",
        "Canvas & Code",
        LeadSource.LINKEDIN,
        LeadStatus.QUALIFIED,
        "190000.00",
        "Strong fit for a design system engagement.",
    ),
    DemoLead(
        "imran-karim",
        "Imran Karim",
        "Kite Finance",
        LeadSource.WEBSITE,
        LeadStatus.QUOTED,
        "280000.00",
        "Reviewing the mobile banking UX proposal.",
    ),
    DemoLead(
        "tasnim-noor",
        "Tasnim Noor",
        "Little Steps",
        LeadSource.REFERRAL,
        LeadStatus.WON,
        "155000.00",
        "Won a responsive enrollment portal project.",
    ),
    DemoLead(
        "sadia-haque",
        "Sadia Haque",
        "Mango Tree Travel",
        LeadSource.OTHER,
        LeadStatus.LOST,
        "110000.00",
        "Project paused because the launch budget changed.",
    ),
    DemoLead(
        "fahim-alam",
        "Fahim Alam",
        "ByteCraft Studio",
        LeadSource.UPWORK,
        LeadStatus.NEW,
        "72000.00",
        "New inquiry for a conversion-focused landing page.",
    ),
    DemoLead(
        "nusrat-jahan",
        "Nusrat Jahan",
        "Alo Foundation",
        LeadSource.EMAIL,
        LeadStatus.CONTACTED,
        "130000.00",
        "Shared nonprofit website goals and content inventory.",
    ),
    DemoLead(
        "omar-faruq",
        "Omar Faruq",
        "Harbor Homes",
        LeadSource.WEBSITE,
        LeadStatus.QUALIFIED,
        "225000.00",
        "Qualified property listing experience redesign.",
    ),
    DemoLead(
        "rima-sultana",
        "Rima Sultana",
        "Bloom Skincare",
        LeadSource.FIVERR,
        LeadStatus.QUOTED,
        "165000.00",
        "Awaiting feedback on the storefront proposal.",
    ),
    DemoLead(
        "adnan-siddique",
        "Adnan Siddique",
        "Metric Works",
        LeadSource.LINKEDIN,
        LeadStatus.WON,
        "340000.00",
        "Analytics dashboard engagement is approved.",
    ),
    DemoLead(
        "mahin-khan",
        "Mahin Khan",
        "City Cycle",
        LeadSource.PHONE,
        LeadStatus.LOST,
        "80000.00",
        "Timing did not align with the planned seasonal release.",
    ),
    DemoLead(
        "sabrina-rahman",
        "Sabrina Rahman",
        "Paper Kite Press",
        LeadSource.REFERRAL,
        LeadStatus.NEW,
        "58000.00",
        "Exploring a catalog and author profile refresh.",
    ),
    DemoLead(
        "jubayer-islam",
        "Jubayer Islam",
        "Cloud Harbor",
        LeadSource.UPWORK,
        LeadStatus.CONTACTED,
        "205000.00",
        "Discovery call completed for B2B account management.",
    ),
    DemoLead(
        "mehreen-ali",
        "Mehreen Ali",
        "Root & Ritual",
        LeadSource.WEBSITE,
        LeadStatus.QUALIFIED,
        "145000.00",
        "Qualified for a subscription commerce redesign.",
    ),
    DemoLead(
        "nafis-ahmed",
        "Nafis Ahmed",
        "Peak HR",
        LeadSource.EMAIL,
        LeadStatus.QUOTED,
        "215000.00",
        "Proposal covers the candidate and employer portals.",
    ),
    DemoLead(
        "anika-zaman",
        "Anika Zaman",
        "Studio Shada",
        LeadSource.LINKEDIN,
        LeadStatus.WON,
        "185000.00",
        "Brand portfolio platform approved for delivery.",
    ),
    DemoLead(
        "tanvir-hasan",
        "Tanvir Hasan",
        "Green Route",
        LeadSource.OTHER,
        LeadStatus.LOST,
        "125000.00",
        "Client postponed the project until next funding cycle.",
    ),
    DemoLead(
        "maliha-ferdous",
        "Maliha Ferdous",
        "Kindred Kitchen",
        LeadSource.FIVERR,
        LeadStatus.NEW,
        "90000.00",
        "New catering marketplace inquiry.",
    ),
    DemoLead(
        "shafin-rahman",
        "Shafin Rahman",
        "Signal Telecom",
        LeadSource.PHONE,
        LeadStatus.CONTACTED,
        "260000.00",
        "Stakeholder list received; schedule solution workshop.",
    ),
    DemoLead(
        "raisa-karim",
        "Raisa Karim",
        "Morrow Legal",
        LeadSource.REFERRAL,
        LeadStatus.QUALIFIED,
        "170000.00",
        "Qualified for a multilingual professional services site.",
    ),
    DemoLead(
        "ashik-chowdhury",
        "Ashik Chowdhury",
        "Delta Solar",
        LeadSource.WEBSITE,
        LeadStatus.QUOTED,
        "295000.00",
        "Commercial dashboard proposal is under review.",
    ),
    DemoLead(
        "sanjida-islam",
        "Sanjida Islam",
        "Quiet Corner",
        LeadSource.EMAIL,
        LeadStatus.WON,
        "135000.00",
        "Membership and events website accepted.",
    ),
    DemoLead(
        "maruf-hossain",
        "Maruf Hossain",
        "Field Notes",
        LeadSource.UPWORK,
        LeadStatus.LOST,
        "105000.00",
        "Lead closed after scope and timeline changed.",
    ),
)

DEMO_QUOTES = (
    DemoQuote(
        "patient-portal",
        "farhana-kabir",
        QuotationStatus.DRAFT,
        2,
        "5.00",
        "7.50",
        "Valid after a technical discovery session.",
        (
            ("Product discovery", "1.000", "45000.00"),
            ("Patient portal UX", "1.000", "120000.00"),
            ("Usability test plan", "1.000", "30000.00"),
        ),
    ),
    DemoQuote(
        "design-system",
        "zara-ahmed",
        QuotationStatus.DRAFT,
        4,
        "0.00",
        "7.50",
        "Includes component documentation and handoff.",
        (
            ("Interface audit", "1.000", "35000.00"),
            ("Design system foundation", "1.000", "125000.00"),
        ),
    ),
    DemoQuote(
        "saas-onboarding",
        "hasan-mahmud",
        QuotationStatus.SENT,
        8,
        "10.00",
        "7.50",
        "Two revision rounds are included.",
        (
            ("Journey mapping", "1.000", "40000.00"),
            ("Onboarding flows", "1.000", "95000.00"),
            ("Prototype validation", "1.000", "35000.00"),
        ),
    ),
    DemoQuote(
        "banking-experience",
        "imran-karim",
        QuotationStatus.SENT,
        12,
        "5.00",
        "10.00",
        "Delivery is planned across three milestones.",
        (
            ("Mobile UX audit", "1.000", "55000.00"),
            ("Core transaction flows", "1.000", "145000.00"),
            ("Design QA", "2.000", "25000.00"),
        ),
    ),
    DemoQuote(
        "learning-platform",
        "laila-chowdhury",
        QuotationStatus.ACCEPTED,
        28,
        "8.00",
        "7.50",
        "Accepted scope for the first product release.",
        (
            ("Learner dashboard", "1.000", "105000.00"),
            ("Course experience", "1.000", "125000.00"),
            ("Responsive design QA", "1.000", "45000.00"),
        ),
    ),
    DemoQuote(
        "enrollment-portal",
        "tasnim-noor",
        QuotationStatus.ACCEPTED,
        21,
        "5.00",
        "7.50",
        "Project kickoff follows the initial payment.",
        (("Enrollment workflow", "1.000", "85000.00"), ("Parent portal", "1.000", "65000.00")),
    ),
    DemoQuote(
        "storefront-refresh",
        "rima-sultana",
        QuotationStatus.REJECTED,
        18,
        "0.00",
        "7.50",
        "Proposal archived after client review.",
        (("Storefront UX", "1.000", "95000.00"), ("Mobile checkout", "1.000", "55000.00")),
    ),
    DemoQuote(
        "candidate-portals",
        "nafis-ahmed",
        QuotationStatus.REJECTED,
        24,
        "10.00",
        "7.50",
        "Scope can be revisited in a future quarter.",
        (
            ("Employer portal", "1.000", "90000.00"),
            ("Candidate portal", "1.000", "90000.00"),
            ("Shared UI kit", "1.000", "35000.00"),
        ),
    ),
)

DEMO_FOLLOWUPS = (
    DemoFollowUp("overdue-roasters", "arif-hossain", -5, 10, "Send the revised campaign timeline."),
    DemoFollowUp(
        "overdue-logistics", "rakib-sarker", -2, 15, "Call to confirm workshop attendees."
    ),
    DemoFollowUp(
        "overdue-foundation", "nusrat-jahan", -1, 11, "Review the content inventory together."
    ),
    DemoFollowUp("today-health", "farhana-kabir", 0, 9, "Confirm discovery session availability."),
    DemoFollowUp(
        "today-travel", "sadia-haque", 0, 14, "Check whether the paused budget has reopened."
    ),
    DemoFollowUp("today-legal", "raisa-karim", 0, 18, "Share the multilingual sitemap outline."),
    DemoFollowUp(
        "upcoming-cloud", "jubayer-islam", 1, 10, "Run the account-management discovery call."
    ),
    DemoFollowUp(
        "upcoming-solar", "ashik-chowdhury", 3, 16, "Collect proposal feedback from operations."
    ),
    DemoFollowUp(
        "upcoming-kitchen", "maliha-ferdous", 7, 11, "Send marketplace examples before the call."
    ),
    DemoFollowUp(
        "completed-education",
        "laila-chowdhury",
        -12,
        13,
        "Confirm signed proposal and kickoff date.",
        True,
    ),
    DemoFollowUp(
        "completed-analytics",
        "adnan-siddique",
        -7,
        10,
        "Receive analytics access requirements.",
        True,
    ),
    DemoFollowUp(
        "completed-studio", "anika-zaman", -3, 17, "Confirm portfolio content handoff.", True
    ),
)


def _demo_id(kind: str, key: str) -> UUID:
    return uuid5(DEMO_NAMESPACE, f"{kind}:{key}")


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


def _reset_demo_business_data(session: Session, user_id: UUID) -> None:
    lead_ids = select(Lead.id).where(Lead.owner_id == user_id)
    quotation_ids = select(Quotation.id).where(Quotation.lead_id.in_(lead_ids))
    session.execute(delete(QuotationItem).where(QuotationItem.quotation_id.in_(quotation_ids)))
    session.execute(delete(FollowUp).where(FollowUp.lead_id.in_(lead_ids)))
    session.execute(delete(Quotation).where(Quotation.lead_id.in_(lead_ids)))
    session.execute(delete(Lead).where(Lead.owner_id == user_id))
    session.flush()


def _create_demo_dataset(
    session: Session,
    user: User,
    settings: Settings,
    anchor: datetime,
) -> None:
    timezone = ZoneInfo(settings.demo_timezone)
    local_anchor = anchor.astimezone(timezone)
    today = local_anchor.date()
    leads: dict[str, Lead] = {}

    for index, definition in enumerate(DEMO_LEADS):
        created_at = (anchor - timedelta(days=45 - index)).astimezone(UTC)
        lead = Lead(
            id=_demo_id("lead", definition.key),
            owner_id=user.id,
            contact_name=definition.contact_name,
            company=definition.company,
            email=f"{definition.key}@example.com",
            phone=f"+880 1700-{100000 + index:06d}",
            source=definition.source,
            status=definition.status,
            estimated_value=Decimal(definition.estimated_value),
            notes=definition.notes,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(lead)
        leads[definition.key] = lead
    session.flush()

    for index, definition in enumerate(DEMO_QUOTES):
        item_inputs = [
            QuotationItemInput(
                description=description,
                quantity=Decimal(quantity),
                unit_price=Decimal(unit_price),
            )
            for description, quantity, unit_price in definition.items
        ]
        discount_percent = Decimal(definition.discount_percent)
        tax_percent = Decimal(definition.tax_percent)
        totals = calculate_quotation(item_inputs, discount_percent, tax_percent)
        issue_date = today - timedelta(days=definition.days_ago)
        created_at = datetime.combine(issue_date, time(9), tzinfo=timezone).astimezone(UTC)
        sent_at = (
            created_at + timedelta(days=1) if definition.status != QuotationStatus.DRAFT else None
        )
        accepted_at = (
            sent_at + timedelta(days=2)
            if definition.status == QuotationStatus.ACCEPTED and sent_at
            else None
        )
        rejected_at = (
            sent_at + timedelta(days=2)
            if definition.status == QuotationStatus.REJECTED and sent_at
            else None
        )
        quotation = Quotation(
            id=_demo_id("quotation", definition.key),
            lead=leads[definition.lead_key],
            quote_number=f"Q-{today.year}-{DEMO_QUOTE_NUMBER_START + index:06d}",
            status=definition.status,
            issue_date=issue_date,
            valid_until=issue_date + timedelta(days=14),
            subtotal=totals.subtotal,
            discount_percent=discount_percent,
            discount_amount=totals.discount_amount,
            tax_percent=tax_percent,
            tax_amount=totals.tax_amount,
            total=totals.total,
            notes=definition.notes,
            sent_at=sent_at,
            accepted_at=accepted_at,
            rejected_at=rejected_at,
            created_at=created_at,
            updated_at=accepted_at or rejected_at or sent_at or created_at,
            items=[
                QuotationItem(
                    id=_demo_id("quotation-item", f"{definition.key}:{item.sort_order}"),
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    line_total=item.line_total,
                    sort_order=item.sort_order,
                )
                for item in totals.items
            ],
        )
        session.add(quotation)

    for definition in DEMO_FOLLOWUPS:
        due_local = datetime.combine(
            today + timedelta(days=definition.day_offset),
            time(definition.hour),
            tzinfo=timezone,
        )
        due_at = due_local.astimezone(UTC)
        completed_at = due_at + timedelta(hours=4) if definition.completed else None
        created_at = min(anchor - timedelta(days=1), due_at - timedelta(days=2))
        session.add(
            FollowUp(
                id=_demo_id("follow-up", definition.key),
                lead=leads[definition.lead_key],
                due_at=due_at,
                note=definition.note,
                is_completed=definition.completed,
                completed_at=completed_at,
                created_at=created_at,
                updated_at=completed_at or created_at,
            )
        )


def seed_demo_data(
    session: Session,
    settings: Settings,
    *,
    reset: bool = False,
    now: datetime | None = None,
) -> SeedResult:
    if reset and settings.environment == "production":
        raise RuntimeError("Demo reset is disabled in production environments.")

    anchor = now or datetime.now(UTC)
    if anchor.tzinfo is None or anchor.utcoffset() is None:
        raise ValueError("The seed anchor must include timezone information.")
    anchor = anchor.astimezone(UTC)
    user, user_created = create_demo_user(session, settings)
    marker_id = _demo_id("lead", DEMO_LEADS[0].key)

    try:
        if reset:
            _reset_demo_business_data(session, user.id)
        elif session.get(Lead, marker_id) is not None:
            return SeedResult(
                user=user,
                user_created=user_created,
                dataset_created=False,
                reset=False,
                lead_count=len(DEMO_LEADS),
                quotation_count=len(DEMO_QUOTES),
                item_count=sum(len(quote.items) for quote in DEMO_QUOTES),
                followup_count=len(DEMO_FOLLOWUPS),
            )

        _create_demo_dataset(session, user, settings, anchor)
        session.commit()
        session.refresh(user)
    except Exception:
        session.rollback()
        raise

    return SeedResult(
        user=user,
        user_created=user_created,
        dataset_created=True,
        reset=reset,
        lead_count=len(DEMO_LEADS),
        quotation_count=len(DEMO_QUOTES),
        item_count=sum(len(quote.items) for quote in DEMO_QUOTES),
        followup_count=len(DEMO_FOLLOWUPS),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare the ClientFlow demo account and data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Replace only the demo user's business data with the canonical dataset.",
    )
    return parser.parse_args()


def main() -> None:
    settings = get_settings()
    args = parse_args()
    with SessionLocal() as session:
        result = seed_demo_data(session, settings, reset=args.reset)

    user_action = "created" if result.user_created else "reused"
    data_action = (
        "reset" if result.reset else ("created" if result.dataset_created else "already present")
    )
    print(
        f"Demo user {user_action}: {result.user.email}. Dataset {data_action}: "
        f"{result.lead_count} leads, {result.quotation_count} quotations, "
        f"{result.item_count} items, {result.followup_count} follow-ups."
    )


if __name__ == "__main__":
    main()
