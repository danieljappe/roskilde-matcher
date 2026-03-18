from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artist import FestivalArtist

logger = logging.getLogger(__name__)

LINEUP_URL = "https://www.roskilde-festival.dk/program/"
FALLBACK_PATH = Path("/data/lineup_fallback.json")


async def scrape_lineup() -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(LINEUP_URL)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        names: list[str] = []

        # Target the h2 card headlines used on the Roskilde program page
        for tag in soup.find_all("h2", class_=lambda c: c and "card_headline" in c):
            text = tag.get_text(strip=True)
            if text and 1 < len(text) < 100:
                names.append(text)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for name in names:
            name = _strip_prefix(name)
            if name not in seen:
                seen.add(name)
                unique.append(name)

        if unique:
            logger.info("Scraped %d artists from lineup page", len(unique))
            return unique

        logger.warning("No artists found via scraping, falling back to lineup_fallback.json")

    except Exception as exc:
        logger.warning("Scraping failed (%s), falling back to lineup_fallback.json", exc)

    return _load_fallback_names()


def _strip_prefix(name: str) -> str:
    return name.removeprefix("Ny!")


def _load_fallback_names() -> list[str]:
    if FALLBACK_PATH.exists():
        data: dict = json.loads(FALLBACK_PATH.read_text())
        return [_strip_prefix(k) for k in data.keys()]
    logger.error("lineup_fallback.json not found at %s", FALLBACK_PATH)
    return []


async def seed_artists(db: AsyncSession) -> int:
    names = await scrape_lineup()
    if not names:
        logger.error("No artists to seed")
        return 0

    inserted = 0
    for i in range(0, len(names), 50):
        batch = names[i : i + 50]
        stmt = (
            insert(FestivalArtist)
            .values([{"name": name, "genres": [], "related_artists": []} for name in batch])
            .on_conflict_do_nothing(index_elements=["name"])
        )
        result = await db.execute(stmt)
        inserted += result.rowcount or 0

    await db.commit()
    logger.info("Seeded %d new artists", inserted)
    return inserted


if __name__ == "__main__":
    import asyncio

    from app.database import AsyncSessionLocal

    async def main() -> None:
        async with AsyncSessionLocal() as db:
            count = await seed_artists(db)
            print(f"Seeded {count} artists")

    asyncio.run(main())
