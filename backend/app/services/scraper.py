from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artist import FestivalArtist

logger = logging.getLogger(__name__)

BASE_URL = "https://www.roskilde-festival.dk"
PROGRAM_URL = f"{BASE_URL}/program/"
FALLBACK_PATH = Path("/data/lineup_fallback.json")



async def scrape_lineup() -> list[dict]:
    """Return list of {name, slug} dicts from the program page."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(PROGRAM_URL)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[dict] = []
        seen: set[str] = set()

        for a_tag in soup.find_all("a", href=re.compile(r"^/program/musik/")):
            h2 = a_tag.find("h2", class_=lambda c: c and "card_headline" in c)
            if not h2:
                continue
            name = _strip_prefix(h2.get_text(strip=True))
            if not name or name in seen:
                continue
            seen.add(name)
            slug = a_tag["href"].rstrip("/").split("/")[-1]
            results.append({"name": name, "slug": slug})

        if results:
            logger.info("Scraped %d artists from program page", len(results))
            return results

        logger.warning("No artists found via scraping, falling back to lineup_fallback.json")

    except Exception as exc:
        logger.warning("Scraping failed (%s), falling back to lineup_fallback.json", exc)

    return _load_fallback_entries()


def _extract_appearances(html: str) -> list:
    key = '"appearences":'
    idx = html.find(key)
    if idx == -1:
        return []
    start = html.index("[", idx + len(key))
    depth = 0
    for i, ch in enumerate(html[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[start : i + 1])
                except json.JSONDecodeError:
                    return []
    return []


async def fetch_schedule(client: httpx.AsyncClient, slug: str) -> dict:
    """Fetch stage/start_time/end_time for one artist page."""
    try:
        url = f"{BASE_URL}/program/musik/{slug}"
        response = await client.get(url)
        response.raise_for_status()
        html = response.text

        appearances = _extract_appearances(html)
        if not appearances:
            return {}


        first = appearances[0]
        stage = first.get("stage")
        start_raw = first.get("startDate")
        end_raw = first.get("endDate")

        return {
            "stage": stage,
            "start_time": datetime.fromisoformat(start_raw) if start_raw else None,
            "end_time": datetime.fromisoformat(end_raw) if end_raw else None,
        }
    except Exception as exc:
        logger.debug("Could not fetch schedule for %r: %s", slug, exc)
        return {}


def _strip_prefix(name: str) -> str:
    return name.removeprefix("Ny!")


def _load_fallback_entries() -> list[dict]:
    if FALLBACK_PATH.exists():
        data: dict = json.loads(FALLBACK_PATH.read_text())
        return [{"name": _strip_prefix(k), "slug": None} for k in data.keys()]
    logger.error("lineup_fallback.json not found at %s", FALLBACK_PATH)
    return []


async def seed_artists(db: AsyncSession) -> int:
    entries = await scrape_lineup()
    if not entries:
        logger.error("No artists to seed")
        return 0

    # Upsert names/slugs
    for i in range(0, len(entries), 50):
        batch = entries[i : i + 50]
        stmt = (
            insert(FestivalArtist)
            .values([{"name": e["name"], "slug": e["slug"], "is_music": True, "genres": [], "related_artists": []} for e in batch])
            .on_conflict_do_update(
                index_elements=["name"],
                set_={
                    "slug": insert(FestivalArtist).excluded.slug,
                    "is_music": insert(FestivalArtist).excluded.is_music,
                },
            )
        )
        await db.execute(stmt)

    await db.commit()
    logger.info("Upserted %d artists", len(entries))

    # Fetch schedule data for artists that have a slug but no start_time yet
    result = await db.execute(
        select(FestivalArtist).where(
            FestivalArtist.slug.isnot(None),
            FestivalArtist.start_time.is_(None),
        )
    )
    to_enrich = list(result.scalars().all())
    logger.info("Fetching schedule for %d artists", len(to_enrich))

    sem = asyncio.Semaphore(5)

    async def _fetch(client: httpx.AsyncClient, artist: FestivalArtist) -> None:
        async with sem:
            schedule = await fetch_schedule(client, artist.slug)
            if schedule:
                artist.stage = schedule.get("stage")
                artist.start_time = schedule.get("start_time")
                artist.end_time = schedule.get("end_time")
            await asyncio.sleep(0.1)

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        await asyncio.gather(*[_fetch(client, a) for a in to_enrich])

    await db.commit()
    logger.info("Schedule enrichment complete")
    return len(entries)


if __name__ == "__main__":
    from app.database import AsyncSessionLocal

    async def main() -> None:
        async with AsyncSessionLocal() as db:
            count = await seed_artists(db)
            print(f"Seeded/updated {count} artists")

    asyncio.run(main())
