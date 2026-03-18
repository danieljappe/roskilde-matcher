from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from thefuzz import fuzz

from app.models.artist import FestivalArtist
from app.services import spotify_client

logger = logging.getLogger(__name__)

FALLBACK_PATH = Path("/data/lineup_fallback.json")
FUZZY_THRESHOLD = 85


def _load_overrides() -> dict[str, str | None]:
    if FALLBACK_PATH.exists():
        return json.loads(FALLBACK_PATH.read_text())
    return {}


async def enrich_all_artists(db: AsyncSession) -> None:
    overrides = _load_overrides()

    # Load unenriched artists
    result = await db.execute(
        select(FestivalArtist).where(FestivalArtist.last_updated.is_(None))
    )
    artists = list(result.scalars().all())

    if not artists:
        logger.info("All artists already enriched")
        return

    logger.info("Enriching %d artists", len(artists))

    # Resolve Spotify IDs
    id_map: dict[int, str] = {}  # artist.id -> spotify_id

    for artist in artists:
        override = overrides.get(artist.name)
        if override:
            id_map[artist.id] = override
            artist.spotify_id = override
            continue

        # Search Spotify
        result = await spotify_client.search_artist(artist.name)
        if result:
            score = fuzz.token_set_ratio(result["name"], artist.name)
            if score >= FUZZY_THRESHOLD:
                id_map[artist.id] = result["id"]
                artist.spotify_id = result["id"]
            else:
                logger.warning(
                    "Fuzzy mismatch for %r: got %r (score %d)", artist.name, result["name"], score
                )
        else:
            logger.warning("No Spotify result for %r", artist.name)

    await db.flush()

    # Fetch genres from Last.fm and images from Spotify single-artist endpoint
    now = datetime.now(UTC)
    batch_count = 0

    async def enrich_single(artist: FestivalArtist) -> None:
        nonlocal batch_count
        genres = await spotify_client.get_lastfm_genres(artist.name)
        artist.genres = genres

        # Fetch image from Spotify single-artist endpoint if we have a spotify_id
        if artist.spotify_id:
            try:
                token = await spotify_client._get_client_credentials_token()
                async with __import__("httpx").AsyncClient() as client:
                    r = await client.get(
                        f"https://api.spotify.com/v1/artists/{artist.spotify_id}",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    if r.status_code == 200:
                        data = r.json()
                        images = data.get("images") or []
                        artist.image_url = images[0]["url"] if images else None
            except Exception:
                pass

        artist.last_updated = now
        batch_count += 1

    # Process in chunks of 10 concurrently to respect Last.fm rate limits
    for i in range(0, len(artists), 10):
        chunk = artists[i : i + 10]
        await asyncio.gather(*[enrich_single(a) for a in chunk])
        if batch_count % 20 == 0:
            await db.commit()
            logger.info("Progress: %d/%d artists enriched", batch_count, len(artists))

    await db.commit()
    logger.info("Enrichment complete. Enriched %d/%d artists", batch_count, len(artists))


if __name__ == "__main__":
    import asyncio

    from app.database import AsyncSessionLocal

    async def main() -> None:
        async with AsyncSessionLocal() as db:
            await enrich_all_artists(db)

    asyncio.run(main())
