"""merchant_settlement_foundation

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-29 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "settlement",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(length=60), nullable=False),
        sa.Column("conversion_id", sa.Integer(), sa.ForeignKey("conversion.id"), nullable=False),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("gross_amount", sa.Float(), nullable=False),
        sa.Column("platform_fee", sa.Float(), nullable=False, server_default="0"),
        sa.Column("net_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("approved_by_admin_id", sa.Integer(), sa.ForeignKey("admin_user.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("reference"),
        sa.UniqueConstraint("conversion_id"),
    )
    op.create_index("ix_settlement_reference", "settlement", ["reference"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_settlement_reference", table_name="settlement")
    op.drop_table("settlement")
