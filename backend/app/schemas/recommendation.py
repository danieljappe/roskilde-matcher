from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.artist import RecommendedArtist


class RecommendationListResponse(BaseModel):
    user_spotify_id: str
    refreshed_at: datetime | None
    results: list[RecommendedArtist]
