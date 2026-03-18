from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserProfile
from app.services import spotify_client

logger = logging.getLogger(__name__)

TIME_RANGES = ["short_term", "medium_term", "long_term"]
RANGE_WEIGHTS = {"short_term": 1.0, "medium_term": 0.85, "long_term": 0.7}


def _build_genre_profile(top_artists: dict[str, list[dict]]) -> dict[str, float]:
    genre_scores: dict[str, float] = {}

    for time_range, artists in top_artists.items():
        weight = RANGE_WEIGHTS[time_range]
        for rank, artist in enumerate(artists):
            rank_decay = 1.0 - (rank / 50.0)
            contribution = weight * rank_decay
            for genre in artist.get("genres", []):
                genre_scores[genre] = genre_scores.get(genre, 0.0) + contribution

    # Normalize to 0..1 range
    if genre_scores:
        max_score = max(genre_scores.values())
        if max_score > 0:
            genre_scores = {g: s / max_score for g, s in genre_scores.items()}

    return genre_scores


async def _enrich_artists_with_genres(
    artists_by_range: dict[str, list[dict]],
) -> dict[str, list[dict]]:
    """Fetch genres for all unique top artists from Last.fm."""
    unique_artists = {a["id"]: a for artists in artists_by_range.values() for a in artists}
    if not unique_artists:
        return artists_by_range

    # Fetch genres concurrently in chunks of 10
    id_to_genres: dict[str, list[str]] = {}
    items = list(unique_artists.items())
    for i in range(0, len(items), 10):
        chunk = items[i : i + 10]
        results = await asyncio.gather(*[
            spotify_client.get_lastfm_genres(a["name"]) for _, a in chunk
        ])
        for (artist_id, _), genres in zip(chunk, results):
            id_to_genres[artist_id] = genres

    enriched: dict[str, list[dict]] = {}
    for time_range, artists in artists_by_range.items():
        enriched[time_range] = [
            {**a, "genres": id_to_genres.get(a["id"], [])} for a in artists
        ]
    return enriched


async def sync_user_profile(
    user_id: int, access_token: str, db: AsyncSession
) -> UserProfile:
    # Fetch all three time ranges concurrently
    short, medium, long_ = await asyncio.gather(
        spotify_client.get_top_artists("short_term", access_token),
        spotify_client.get_top_artists("medium_term", access_token),
        spotify_client.get_top_artists("long_term", access_token),
    )

    top_artists = {
        "short_term": short,
        "medium_term": medium,
        "long_term": long_,
    }

    # Enrich with genres from Last.fm (Spotify removed genres from their API)
    top_artists = await _enrich_artists_with_genres(top_artists)

    genre_profile = _build_genre_profile(top_artists)

    result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    user = result.scalar_one()

    user.top_artists = top_artists
    user.genre_profile = genre_profile
    user.refreshed_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(user)

    logger.info(
        "Synced user %d: %d genres, %d/%d/%d top artists",
        user_id,
        len(genre_profile),
        len(short),
        len(medium),
        len(long_),
    )
    return user
