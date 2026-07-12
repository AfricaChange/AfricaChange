"""reporting_foundation

Revision ID: 4c8f0d9e1a2b
Revises: 698184e64da9
Create Date: 2026-07-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4c8f0d9e1a2b"
down_revision: Union[str, None] = "698184e64da9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("conversion") as batch:
        batch.add_column(sa.Column("quote_source_amount", sa.Numeric(24, 8), nullable=True))
        batch.add_column(sa.Column("quote_target_amount", sa.Numeric(24, 8), nullable=True))
        batch.add_column(sa.Column("client_rate", sa.Numeric(24, 8), nullable=True))
        batch.add_column(sa.Column("execution_mode", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("margin_estimated", sa.Numeric(24, 8), nullable=True))
        batch.add_column(sa.Column("offer_snapshot", sa.JSON(), nullable=True))

    op.create_table(
        "conversion_execution",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversion_id", sa.Integer(), sa.ForeignKey("conversion.id"), nullable=False),
        sa.Column("execution_reference", sa.String(length=100), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("provider_code", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("payin_reference", sa.String(length=100), nullable=True),
        sa.Column("payout_reference", sa.String(length=100), nullable=True),
        sa.Column("payin_status", sa.String(length=50), nullable=True),
        sa.Column("payout_status", sa.String(length=50), nullable=True),
        sa.Column("amount_source", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("amount_destination", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("provider_fees", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("execution_cost", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.String(length=255), nullable=True),
        sa.Column("raw_context", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("conversion_id", name="uq_conversion_execution_conversion_id"),
        sa.UniqueConstraint("execution_reference", name="uq_conversion_execution_reference"),
    )
    op.create_index(
        "ix_conversion_execution_conversion_id",
        "conversion_execution",
        ["conversion_id"],
        unique=True,
    )
    op.create_index(
        "ix_conversion_execution_execution_reference",
        "conversion_execution",
        ["execution_reference"],
        unique=True,
    )
    op.create_index(
        "ix_conversion_execution_status",
        "conversion_execution",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_conversion_execution_status", table_name="conversion_execution")
    op.drop_index("ix_conversion_execution_execution_reference", table_name="conversion_execution")
    op.drop_index("ix_conversion_execution_conversion_id", table_name="conversion_execution")
    op.drop_table("conversion_execution")

    with op.batch_alter_table("conversion") as batch:
        batch.drop_column("offer_snapshot")
        batch.drop_column("margin_estimated")
        batch.drop_column("execution_mode")
        batch.drop_column("client_rate")
        batch.drop_column("quote_target_amount")
        batch.drop_column("quote_source_amount")
