"""admin_wallet_actions

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-28 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_wallet_action",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("requested_by_admin_id", sa.Integer(), sa.ForeignKey("utilisateur.id"), nullable=False),
        sa.Column("approved_by_admin_id", sa.Integer(), sa.ForeignKey("utilisateur.id"), nullable=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("currency_code", sa.String(length=10), sa.ForeignKey("currency.code"), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(24, 8), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("session_identifier", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("reference"),
    )
    op.create_index("ix_admin_wallet_action_requested_by_admin_id", "admin_wallet_action", ["requested_by_admin_id"], unique=False)
    op.create_index("ix_admin_wallet_action_approved_by_admin_id", "admin_wallet_action", ["approved_by_admin_id"], unique=False)
    op.create_index("ix_admin_wallet_action_merchant_id", "admin_wallet_action", ["merchant_id"], unique=False)
    op.create_index("ix_admin_wallet_action_currency_code", "admin_wallet_action", ["currency_code"], unique=False)
    op.create_index("ix_admin_wallet_action_reference", "admin_wallet_action", ["reference"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_admin_wallet_action_reference", table_name="admin_wallet_action")
    op.drop_index("ix_admin_wallet_action_currency_code", table_name="admin_wallet_action")
    op.drop_index("ix_admin_wallet_action_merchant_id", table_name="admin_wallet_action")
    op.drop_index("ix_admin_wallet_action_approved_by_admin_id", table_name="admin_wallet_action")
    op.drop_index("ix_admin_wallet_action_requested_by_admin_id", table_name="admin_wallet_action")
    op.drop_table("admin_wallet_action")
