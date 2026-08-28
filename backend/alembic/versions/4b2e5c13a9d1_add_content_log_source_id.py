"""Add canonical source id to content logs

Revision ID: 4b2e5c13a9d1
Revises: 9f7a35f02e18
Create Date: 2026-08-25 22:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4b2e5c13a9d1"
down_revision: Union[str, Sequence[str], None] = "9f7a35f02e18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("content_logs", sa.Column("source_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_content_logs_source_id"), "content_logs", ["source_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_content_logs_source_id"), table_name="content_logs")
    op.drop_column("content_logs", "source_id")
