from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artist import FestivalArtist
from app.models.recommendation import UserRecommendation
from app.models.user import UserProfile
from app.services.genre_analyzer import compute_genre_match

logger = logging.getLogger(__name__)

WEIGHT_DIRECT = 0.65
WEIGHT_GENRE = 0.35
WEIGHT_DISCOVERY = 0.0  # related-artists endpoint deprecated by Spotify Nov 2024

DISCOVERY_MAP = {0: 0.0, 1: 0.3, 2: 0.65}
# Long-term presence weighted highest — recent spikes shouldn't beat sustained favourites.
# Scores are additive across ranges so consistent presence compounds; clamped to 1.0.
RANGE_WEIGHTS = {"short_term": 0.5, "medium_term": 0.8, "long_term": 1.0}


def _compute_direct_match(artist_spotify_id: str | None, artist_name: str, top_artists: dict) -> float:
    total = 0.0
    for time_range, weight in RANGE_WEIGHTS.items():
        artists_in_range = top_artists.get(time_range, [])
        for rank, a in enumerate(artists_in_range):
            id_match = artist_spotify_id and a.get("id") == artist_spotify_id
            name_match = a.get("name", "").lower() == artist_name.lower()
            if id_match or name_match:
                rank_decay = 1.0 - (rank / 50.0)
                total += weight * rank_decay
                break  # only count each range once per artist
    return min(total, 1.0)


def _compute_discovery_score(related_artists: list[dict], user_artist_ids: set[str]) -> float:
    connections = sum(1 for r in related_artists if r.get("id") in user_artist_ids)
    return DISCOVERY_MAP.get(min(connections, 2), 1.0) if connections < 3 else 1.0


async def compute_recommendations(user_id: int, db: AsyncSession) -> list[dict]:
    # Load user profile
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.error("User %d not found", user_id)
        return []

    top_artists: dict = user.top_artists or {}
    genre_profile: dict = user.genre_profile or {}

    # Build flat set of all user Spotify artist IDs
    user_artist_ids: set[str] = set()
    for artists in top_artists.values():
        for a in artists:
            if a.get("id"):
                user_artist_ids.add(a["id"])

    # Load all enriched festival artists (last_updated set by enrichment)
    result = await db.execute(
        select(FestivalArtist).where(FestivalArtist.last_updated.isnot(None))
    )
    artists = list(result.scalars().all())

    if not artists:
        logger.warning("No enriched festival artists found")
        return []

    rows: list[dict] = []

    for artist in artists:
        direct = _compute_direct_match(artist.spotify_id, artist.name, top_artists)
        genre = compute_genre_match(genre_profile, artist.genres or [])
        discovery = _compute_discovery_score(artist.related_artists or [], user_artist_ids)

        composite = WEIGHT_DIRECT * direct + WEIGHT_GENRE * genre + WEIGHT_DISCOVERY * discovery

        rows.append(
            {
                "user_id": user_id,
                "festival_artist_id": artist.id,
                "composite_score": round(composite, 4),
                "genre_match_score": round(genre, 4),
                "artist_match_score": round(direct, 4),
                "discovery_score": round(discovery, 4),
            }
        )

    # Bulk upsert
    if rows:
        stmt = pg_insert(UserRecommendation).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "festival_artist_id"],
            set_={
                "composite_score": stmt.excluded.composite_score,
                "genre_match_score": stmt.excluded.genre_match_score,
                "artist_match_score": stmt.excluded.artist_match_score,
                "discovery_score": stmt.excluded.discovery_score,
            },
        )
        await db.execute(stmt)
        await db.commit()

    logger.info("Computed %d recommendations for user %d", len(rows), user_id)
    return sorted(rows, key=lambda r: r["composite_score"], reverse=True)
