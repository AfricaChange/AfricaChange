"""disputes_and_merchant_suspension

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("merchant") as batch:
        batch.add_column(sa.Column("suspended_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("suspension_reason", sa.String(length=255), nullable=True))

    op.create_table(
        "dispute",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(length=60), nullable=False),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transaction.id"), nullable=True),
        sa.Column("conversion_id", sa.Integer(), sa.ForeignKey("conversion.id"), nullable=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchant.id"), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("opened_by_admin_id", sa.Integer(), sa.ForeignKey("admin_user.id"), nullable=True),
        sa.Column("resolved_by_admin_id", sa.Integer(), sa.ForeignKey("admin_user.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("reference"),
    )
    op.create_index("ix_dispute_reference", "dispute", ["reference"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_dispute_reference", table_name="dispute")
    op.drop_table("dispute")
    with op.batch_alter_table("merchant") as batch:
        batch.drop_column("suspension_reason")
        batch.drop_column("suspended_at")
