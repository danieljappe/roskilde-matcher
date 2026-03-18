from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserMeResponse(BaseModel):
    spotify_id: str
    display_name: str | None
    refreshed_at: datetime | None
    top_artists: dict = {}
    genre_profile: dict = {}
