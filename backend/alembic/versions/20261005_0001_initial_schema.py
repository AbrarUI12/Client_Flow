"""Create the initial ClientFlow schema.

Revision ID: 20261005_0001
Revises:
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261005_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.schema.CreateSequence(sa.Sequence("quotation_number_seq", start=1)))

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("business_name", sa.String(length=150), nullable=False),
        sa.Column("business_address", sa.Text(), nullable=False),
        sa.Column("business_phone", sa.String(length=50), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(currency_code) = 3 AND currency_code = upper(currency_code)",
            name="ck_users_currency_code_format",
        ),
        sa.CheckConstraint("email = lower(email)", name="ck_users_email_normalized"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "leads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("contact_name", sa.String(length=100), nullable=False),
        sa.Column("company", sa.String(length=150), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column(
            "source",
            sa.Enum(
                "WEBSITE",
                "REFERRAL",
                "LINKEDIN",
                "UPWORK",
                "FIVERR",
                "EMAIL",
                "PHONE",
                "OTHER",
                name="lead_source",
                native_enum=False,
                create_constraint=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "NEW",
                "CONTACTED",
                "QUALIFIED",
                "QUOTED",
                "WON",
                "LOST",
                name="lead_status",
                native_enum=False,
                create_constraint=False,
            ),
            server_default=sa.text("'NEW'"),
            nullable=False,
        ),
        sa.Column(
            "estimated_value",
            sa.Numeric(precision=14, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "estimated_value >= 0",
            name="ck_leads_estimated_value_nonnegative",
        ),
        sa.CheckConstraint(
            "source IS NULL OR source IN "
            "('WEBSITE', 'REFERRAL', 'LINKEDIN', 'UPWORK', 'FIVERR', 'EMAIL', 'PHONE', 'OTHER')",
            name="ck_leads_source_values",
        ),
        sa.CheckConstraint(
            "status IN ('NEW', 'CONTACTED', 'QUALIFIED', 'QUOTED', 'WON', 'LOST')",
            name="ck_leads_status_values",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_leads_owner_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_leads"),
    )
    op.create_index("ix_leads_created_at", "leads", ["created_at"])
    op.create_index("ix_leads_is_archived", "leads", ["is_archived"])
    op.create_index(
        "ix_leads_owner_active_created",
        "leads",
        ["owner_id", "is_archived", "created_at"],
    )
    op.create_index("ix_leads_owner_id", "leads", ["owner_id"])
    op.create_index("ix_leads_owner_status", "leads", ["owner_id", "status"])
    op.create_index("ix_leads_status", "leads", ["status"])

    op.create_table(
        "quotations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("quote_number", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "SENT",
                "ACCEPTED",
                "REJECTED",
                name="quotation_status",
                native_enum=False,
                create_constraint=False,
            ),
            server_default=sa.text("'DRAFT'"),
            nullable=False,
        ),
        sa.Column("issue_date", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=14, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "discount_percent",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "discount_amount",
            sa.Numeric(precision=14, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "tax_percent",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "tax_amount",
            sa.Numeric(precision=14, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "total",
            sa.Numeric(precision=14, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "discount_amount >= 0",
            name="ck_quotations_discount_amount_nonnegative",
        ),
        sa.CheckConstraint(
            "discount_percent >= 0 AND discount_percent <= 100",
            name="ck_quotations_discount_percent_range",
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SENT', 'ACCEPTED', 'REJECTED')",
            name="ck_quotations_status_values",
        ),
        sa.CheckConstraint("subtotal >= 0", name="ck_quotations_subtotal_nonnegative"),
        sa.CheckConstraint("tax_amount >= 0", name="ck_quotations_tax_amount_nonnegative"),
        sa.CheckConstraint(
            "tax_percent >= 0 AND tax_percent <= 100",
            name="ck_quotations_tax_percent_range",
        ),
        sa.CheckConstraint("total >= 0", name="ck_quotations_total_nonnegative"),
        sa.CheckConstraint(
            "valid_until >= issue_date",
            name="ck_quotations_valid_date_range",
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
            name="fk_quotations_lead_id_leads",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_quotations"),
        sa.UniqueConstraint("quote_number", name="uq_quotations_quote_number"),
    )
    op.create_index("ix_quotations_created_at", "quotations", ["created_at"])
    op.create_index("ix_quotations_lead_id", "quotations", ["lead_id"])
    op.create_index("ix_quotations_lead_status", "quotations", ["lead_id", "status"])
    op.create_index("ix_quotations_status", "quotations", ["status"])

    op.create_table(
        "follow_ups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(is_completed = false AND completed_at IS NULL) OR "
            "(is_completed = true AND completed_at IS NOT NULL)",
            name="ck_follow_ups_completion_consistency",
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
            name="fk_follow_ups_lead_id_leads",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_follow_ups"),
    )
    op.create_index("ix_follow_ups_created_at", "follow_ups", ["created_at"])
    op.create_index("ix_follow_ups_due_at", "follow_ups", ["due_at"])
    op.create_index("ix_follow_ups_is_completed", "follow_ups", ["is_completed"])
    op.create_index("ix_follow_ups_lead_id", "follow_ups", ["lead_id"])
    op.create_index(
        "ix_follow_ups_pending_due",
        "follow_ups",
        ["is_completed", "due_at"],
    )

    op.create_table(
        "quotation_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quotation_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "line_total >= 0",
            name="ck_quotation_items_line_total_nonnegative",
        ),
        sa.CheckConstraint("quantity > 0", name="ck_quotation_items_quantity_positive"),
        sa.CheckConstraint(
            "sort_order >= 0",
            name="ck_quotation_items_sort_order_nonnegative",
        ),
        sa.CheckConstraint(
            "unit_price >= 0",
            name="ck_quotation_items_unit_price_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["quotation_id"],
            ["quotations.id"],
            name="fk_quotation_items_quotation_id_quotations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_quotation_items"),
        sa.UniqueConstraint(
            "quotation_id",
            "sort_order",
            name="uq_quotation_items_quotation_sort_order",
        ),
    )
    op.create_index(
        "ix_quotation_items_quotation_id",
        "quotation_items",
        ["quotation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_quotation_items_quotation_id", table_name="quotation_items")
    op.drop_table("quotation_items")

    op.drop_index("ix_follow_ups_pending_due", table_name="follow_ups")
    op.drop_index("ix_follow_ups_lead_id", table_name="follow_ups")
    op.drop_index("ix_follow_ups_is_completed", table_name="follow_ups")
    op.drop_index("ix_follow_ups_due_at", table_name="follow_ups")
    op.drop_index("ix_follow_ups_created_at", table_name="follow_ups")
    op.drop_table("follow_ups")

    op.drop_index("ix_quotations_status", table_name="quotations")
    op.drop_index("ix_quotations_lead_status", table_name="quotations")
    op.drop_index("ix_quotations_lead_id", table_name="quotations")
    op.drop_index("ix_quotations_created_at", table_name="quotations")
    op.drop_table("quotations")

    op.drop_index("ix_leads_status", table_name="leads")
    op.drop_index("ix_leads_owner_status", table_name="leads")
    op.drop_index("ix_leads_owner_id", table_name="leads")
    op.drop_index("ix_leads_owner_active_created", table_name="leads")
    op.drop_index("ix_leads_is_archived", table_name="leads")
    op.drop_index("ix_leads_created_at", table_name="leads")
    op.drop_table("leads")

    op.drop_table("users")
    op.execute(sa.schema.DropSequence(sa.Sequence("quotation_number_seq")))
