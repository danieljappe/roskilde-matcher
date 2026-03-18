from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FestivalArtist(Base):
    __tablename__ = "festival_artists"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    spotify_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    genres: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="'[]'::jsonb")
    popularity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_artists: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="'[]'::jsonb")
    last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
