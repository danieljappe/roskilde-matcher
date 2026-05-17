from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FestivalArtistBase(BaseModel):
    id: int
    name: str
    genres: list[str]
    popularity: int | None
    image_url: str | None
    spotify_id: str | None
    stage: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_music: bool = True

    model_config = {"from_attributes": True}


class FestivalArtistDetail(FestivalArtistBase):
    related_artists: list[dict]


class RecommendedArtist(FestivalArtistBase):
    composite_score: float
    genre_match_score: float
    artist_match_score: float
    discovery_score: float
