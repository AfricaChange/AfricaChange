"""hybrid_liquidity_foundation

Revision ID: a1b2c3d4e5f6
Revises: 698184e64da9
Create Date: 2026-05-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "698184e64da9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "merchant",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("nom", sa.String(length=120), nullable=False),
        sa.Column("telephone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("pays", sa.String(length=10), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("verifie", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("solde_disponible", sa.Float(), nullable=False, server_default="0"),
        sa.Column("solde_verrouille", sa.Float(), nullable=False, server_default="0"),
        sa.Column("min_ticket", sa.Float(), nullable=False, server_default="0"),
        sa.Column("max_ticket", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("telephone"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_merchant_code", "merchant", ["code"], unique=True)

    op.create_table(
        "merchant_rate",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchant.id"), nullable=False),
        sa.Column("from_currency", sa.String(length=10), nullable=False),
        sa.Column("to_currency", sa.String(length=10), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "merchant_id",
            "from_currency",
            "to_currency",
            name="uq_merchant_rate_pair",
        ),
    )

    with op.batch_alter_table("conversion") as batch:
        batch.add_column(sa.Column("liquidity_source_type", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("risk_bearer", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("merchant_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("merchant_rate_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("assigned_rate", sa.Float(), nullable=True))
        batch.add_column(sa.Column("platform_fee", sa.Float(), nullable=True))
        batch.add_column(sa.Column("locked_amount", sa.Float(), nullable=True))
        batch.add_column(sa.Column("settlement_status", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("selection_reason", sa.String(length=255), nullable=True))
        batch.create_foreign_key("fk_conversion_merchant", "merchant", ["merchant_id"], ["id"])
        batch.create_foreign_key(
            "fk_conversion_merchant_rate",
            "merchant_rate",
            ["merchant_rate_id"],
            ["id"],
        )

    op.execute("UPDATE conversion SET liquidity_source_type = 'platform' WHERE liquidity_source_type IS NULL")
    op.execute("UPDATE conversion SET risk_bearer = 'platform' WHERE risk_bearer IS NULL")
    op.execute("UPDATE conversion SET platform_fee = 0 WHERE platform_fee IS NULL")
    op.execute("UPDATE conversion SET locked_amount = 0 WHERE locked_amount IS NULL")
    op.execute("UPDATE conversion SET settlement_status = 'pending' WHERE settlement_status IS NULL")

    with op.batch_alter_table("conversion") as batch:
        batch.alter_column("liquidity_source_type", existing_type=sa.String(length=20), nullable=False)
        batch.alter_column("risk_bearer", existing_type=sa.String(length=20), nullable=False)
        batch.alter_column("platform_fee", existing_type=sa.Float(), nullable=False)
        batch.alter_column("locked_amount", existing_type=sa.Float(), nullable=False)
        batch.alter_column("settlement_status", existing_type=sa.String(length=20), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("conversion") as batch:
        batch.drop_constraint("fk_conversion_merchant_rate", type_="foreignkey")
        batch.drop_constraint("fk_conversion_merchant", type_="foreignkey")
        batch.drop_column("selection_reason")
        batch.drop_column("settlement_status")
        batch.drop_column("locked_amount")
        batch.drop_column("platform_fee")
        batch.drop_column("assigned_rate")
        batch.drop_column("merchant_rate_id")
        batch.drop_column("merchant_id")
        batch.drop_column("risk_bearer")
        batch.drop_column("liquidity_source_type")

    op.drop_table("merchant_rate")
    op.drop_index("ix_merchant_code", table_name="merchant")
    op.drop_table("merchant")
