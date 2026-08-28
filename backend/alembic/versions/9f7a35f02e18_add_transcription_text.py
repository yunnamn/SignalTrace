"""Add transcription text field

Revision ID: 9f7a35f02e18
Revises: ef5d7ec39335
Create Date: 2026-08-25 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f7a35f02e18"
down_revision: Union[str, Sequence[str], None] = "ef5d7ec39335"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("content_logs", sa.Column("transcription_text", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("content_logs", "transcription_text")
