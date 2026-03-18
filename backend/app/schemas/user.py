from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    spotify_id: str
    display_name: str | None
    genre_profile: dict[str, float]
    refreshed_at: datetime | None

    model_config = {"from_attributes": True}
