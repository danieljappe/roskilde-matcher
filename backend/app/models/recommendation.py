from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRecommendation(Base):
    __tablename__ = "user_recommendations"
    __table_args__ = (UniqueConstraint("user_id", "festival_artist_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    festival_artist_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("festival_artists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    genre_match_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    artist_match_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    discovery_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["UserProfile"] = relationship("UserProfile", backref="recommendations")
    festival_artist: Mapped["FestivalArtist"] = relationship("FestivalArtist", backref="recommendations")
