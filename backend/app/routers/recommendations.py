from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.recommendation import UserRecommendation
from app.models.user import UserProfile
from app.schemas.artist import RecommendedArtist
from app.schemas.recommendation import RecommendationListResponse
from app.services import matching_engine, user_sync

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _build_response(user: UserProfile, recs: list[UserRecommendation]) -> RecommendationListResponse:
    results = [
        RecommendedArtist(
            id=rec.festival_artist.id,
            name=rec.festival_artist.name,
            genres=rec.festival_artist.genres or [],
            popularity=rec.festival_artist.popularity,
            image_url=rec.festival_artist.image_url,
            spotify_id=rec.festival_artist.spotify_id,
            composite_score=rec.composite_score,
            genre_match_score=rec.genre_match_score,
            artist_match_score=rec.artist_match_score,
            discovery_score=rec.discovery_score,
        )
        for rec in recs
    ]
    return RecommendationListResponse(
        user_spotify_id=user.spotify_id,
        refreshed_at=user.refreshed_at,
        results=results,
    )


async def _load_recs(user_id: int, limit: int, db: AsyncSession) -> list[UserRecommendation]:
    result = await db.execute(
        select(UserRecommendation)
        .where(UserRecommendation.user_id == user_id)
        .options(selectinload(UserRecommendation.festival_artist))
        .order_by(UserRecommendation.composite_score.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("", response_model=RecommendationListResponse)
async def get_recommendations(
    request: Request,
    limit: int = 100,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationListResponse:
    """Return cached recommendations; auto-sync if none exist yet."""
    recs = await _load_recs(user.id, limit, db)

    if not recs or not user.refreshed_at:
        access_token = request.session.get("access_token")
        if access_token:
            await user_sync.sync_user_profile(user.id, access_token, db)
        await matching_engine.compute_recommendations(user.id, db)
        recs = await _load_recs(user.id, limit, db)

    return _build_response(user, recs)


@router.post("/refresh", response_model=RecommendationListResponse)
async def refresh_recommendations(
    request: Request,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationListResponse:
    """Force re-sync from Spotify and recompute all scores."""
    access_token = request.session.get("access_token")
    if access_token:
        await user_sync.sync_user_profile(user.id, access_token, db)

    await matching_engine.compute_recommendations(user.id, db)
    recs = await _load_recs(user.id, 100, db)
    return _build_response(user, recs)


@router.get("/genres", response_model=dict)
async def get_genre_profile(
    user: UserProfile = Depends(get_current_user),
) -> dict:
    """Return top 20 genres from user profile for radar chart."""
    profile: dict[str, float] = user.genre_profile or {}
    top = sorted(profile.items(), key=lambda x: x[1], reverse=True)[:20]
    return {"genres": [{"name": g, "score": round(s, 4)} for g, s in top]}


@router.post("/sync", response_model=dict)
async def sync_profile(
    request: Request,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Sync user's Spotify top artists and rebuild genre profile."""
    from fastapi import HTTPException  # noqa: PLC0415

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token in session")

    await user_sync.sync_user_profile(user.id, access_token, db)
    return {"status": "synced"}
