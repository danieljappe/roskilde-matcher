from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from thefuzz import fuzz

from app.database import get_db
from app.models.artist import FestivalArtist
from app.schemas.artist import FestivalArtistBase, FestivalArtistDetail

router = APIRouter(prefix="/artists", tags=["artists"])


@router.get("", response_model=list[FestivalArtistBase])
async def list_artists(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[FestivalArtistBase]:
    result = await db.execute(
        select(FestivalArtist).order_by(FestivalArtist.name).limit(limit).offset(offset)
    )
    artists = result.scalars().all()
    return [
        FestivalArtistBase(
            id=a.id,
            name=a.name,
            genres=a.genres or [],
            popularity=a.popularity,
            image_url=a.image_url,
            spotify_id=a.spotify_id,
        )
        for a in artists
    ]


@router.get("/search", response_model=list[FestivalArtistBase])
async def search_artists(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[FestivalArtistBase]:
    result = await db.execute(select(FestivalArtist))
    all_artists = result.scalars().all()

    scored = [
        (fuzz.token_set_ratio(q.lower(), a.name.lower()), a)
        for a in all_artists
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [a for score, a in scored if score >= 40][:limit]

    return [
        FestivalArtistBase(
            id=a.id,
            name=a.name,
            genres=a.genres or [],
            popularity=a.popularity,
            image_url=a.image_url,
            spotify_id=a.spotify_id,
        )
        for a in top
    ]


@router.get("/{artist_id}", response_model=FestivalArtistDetail)
async def get_artist(
    artist_id: int,
    db: AsyncSession = Depends(get_db),
) -> FestivalArtistDetail:
    result = await db.execute(select(FestivalArtist).where(FestivalArtist.id == artist_id))
    artist = result.scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    return FestivalArtistDetail(
        id=artist.id,
        name=artist.name,
        genres=artist.genres or [],
        popularity=artist.popularity,
        image_url=artist.image_url,
        spotify_id=artist.spotify_id,
        related_artists=artist.related_artists or [],
    )
