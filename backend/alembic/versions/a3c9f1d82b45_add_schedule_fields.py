"""add_schedule_fields

Revision ID: a3c9f1d82b45
Revises: f001e0d53473
Create Date: 2026-05-17

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3c9f1d82b45"
down_revision: Union[str, None] = "f001e0d53473"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("festival_artists", sa.Column("slug", sa.String(255), nullable=True))
    op.add_column("festival_artists", sa.Column("stage", sa.String(255), nullable=True))
    op.add_column("festival_artists", sa.Column("start_time", sa.DateTime(timezone=False), nullable=True))
    op.add_column("festival_artists", sa.Column("end_time", sa.DateTime(timezone=False), nullable=True))
    op.create_unique_constraint("uq_festival_artists_slug", "festival_artists", ["slug"])


def downgrade() -> None:
    op.drop_constraint("uq_festival_artists_slug", "festival_artists", type_="unique")
    op.drop_column("festival_artists", "end_time")
    op.drop_column("festival_artists", "start_time")
    op.drop_column("festival_artists", "stage")
    op.drop_column("festival_artists", "slug")
