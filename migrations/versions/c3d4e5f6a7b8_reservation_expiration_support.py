"""reservation_expiration_support

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-29 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("conversion") as batch:
        batch.add_column(sa.Column("reserved_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("conversion") as batch:
        batch.drop_column("reserved_until")
