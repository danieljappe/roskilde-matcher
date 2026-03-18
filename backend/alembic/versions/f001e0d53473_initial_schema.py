"""initial_schema

Revision ID: f001e0d53473
Revises:
Create Date: 2026-03-16

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f001e0d53473"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "festival_artists",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("spotify_id", sa.String(64), nullable=True),
        sa.Column("genres", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("popularity", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("related_artists", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("spotify_id"),
    )
    op.create_index("ix_festival_artists_name", "festival_artists", ["name"])
    op.create_index("ix_festival_artists_spotify_id", "festival_artists", ["spotify_id"])

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("spotify_id", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("genre_profile", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("top_artists", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("spotify_id"),
    )
    op.create_index("ix_user_profiles_spotify_id", "user_profiles", ["spotify_id"])

    op.create_table(
        "user_recommendations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("festival_artist_id", sa.BigInteger(), nullable=False),
        sa.Column("composite_score", sa.Float(), nullable=False),
        sa.Column("genre_match_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("artist_match_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("discovery_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["festival_artist_id"], ["festival_artists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "festival_artist_id"),
    )
    op.create_index("ix_user_recommendations_user_id", "user_recommendations", ["user_id"])
    op.create_index("ix_user_recommendations_festival_artist_id", "user_recommendations", ["festival_artist_id"])


def downgrade() -> None:
    op.drop_index("ix_user_recommendations_festival_artist_id", "user_recommendations")
    op.drop_index("ix_user_recommendations_user_id", "user_recommendations")
    op.drop_table("user_recommendations")
    op.drop_index("ix_user_profiles_spotify_id", "user_profiles")
    op.drop_table("user_profiles")
    op.drop_index("ix_festival_artists_spotify_id", "festival_artists")
    op.drop_index("ix_festival_artists_name", "festival_artists")
    op.drop_table("festival_artists")
