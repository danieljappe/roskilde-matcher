"""add_is_music

Revision ID: b7e2a3c10d54
Revises: a3c9f1d82b45
Create Date: 2026-05-17

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7e2a3c10d54"
down_revision: Union[str, None] = "a3c9f1d82b45"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "festival_artists",
        sa.Column("is_music", sa.Boolean(), nullable=False, server_default="false"),
    )
    # All artists with a slug were scraped from /program/musik/ — mark them as music
    op.execute("UPDATE festival_artists SET is_music = TRUE WHERE slug IS NOT NULL")


def downgrade() -> None:
    op.drop_column("festival_artists", "is_music")
