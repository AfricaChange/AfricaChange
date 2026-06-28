"""multi_currency_wallet_foundation

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "currency",
        sa.Column("code", sa.String(length=10), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("decimal_places", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "merchant_balance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("currency_code", sa.String(length=10), sa.ForeignKey("currency.code"), nullable=False),
        sa.Column("available_balance", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("locked_balance", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("pending_balance", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("merchant_id", "currency_code", name="uq_merchant_balance_currency"),
    )
    op.create_index("ix_merchant_balance_merchant_id", "merchant_balance", ["merchant_id"], unique=False)
    op.create_index("ix_merchant_balance_currency_code", "merchant_balance", ["currency_code"], unique=False)

    op.create_table(
        "wallet_entry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("currency_code", sa.String(length=10), sa.ForeignKey("currency.code"), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=False),
        sa.Column("operation", sa.String(length=30), nullable=False),
        sa.Column("balance_type", sa.String(length=20), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Numeric(24, 8), nullable=False),
        sa.Column("before_balance", sa.Numeric(24, 8), nullable=False),
        sa.Column("after_balance", sa.Numeric(24, 8), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transaction.id"), nullable=True),
        sa.Column("conversion_id", sa.Integer(), sa.ForeignKey("conversion.id"), nullable=True),
        sa.Column("settlement_id", sa.Integer(), sa.ForeignKey("settlement.id"), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_wallet_entry_merchant_id", "wallet_entry", ["merchant_id"], unique=False)
    op.create_index("ix_wallet_entry_currency_code", "wallet_entry", ["currency_code"], unique=False)
    op.create_index("ix_wallet_entry_reference", "wallet_entry", ["reference"], unique=False)

    currency_table = sa.table(
        "currency",
        sa.column("code", sa.String(length=10)),
        sa.column("name", sa.String(length=50)),
        sa.column("symbol", sa.String(length=10)),
        sa.column("decimal_places", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        currency_table,
        [
            {"code": "GNF", "name": "Guinean Franc", "symbol": "FG", "decimal_places": 0, "is_active": True},
            {"code": "CFA", "name": "West African CFA Franc", "symbol": "CFA", "decimal_places": 0, "is_active": True},
            {"code": "XOF", "name": "West African CFA Franc", "symbol": "CFA", "decimal_places": 0, "is_active": True},
            {"code": "USD", "name": "US Dollar", "symbol": "$", "decimal_places": 2, "is_active": True},
            {"code": "EUR", "name": "Euro", "symbol": "EUR", "decimal_places": 2, "is_active": True},
            {"code": "CDF", "name": "Congolese Franc", "symbol": "FC", "decimal_places": 0, "is_active": True},
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_wallet_entry_reference", table_name="wallet_entry")
    op.drop_index("ix_wallet_entry_currency_code", table_name="wallet_entry")
    op.drop_index("ix_wallet_entry_merchant_id", table_name="wallet_entry")
    op.drop_table("wallet_entry")

    op.drop_index("ix_merchant_balance_currency_code", table_name="merchant_balance")
    op.drop_index("ix_merchant_balance_merchant_id", table_name="merchant_balance")
    op.drop_table("merchant_balance")

    op.drop_table("currency")
