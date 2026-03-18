from __future__ import annotations

import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import UserProfile
from app.schemas.auth import UserMeResponse
from app.services import spotify_client

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


class CallbackBody(BaseModel):
    code: str
    state: str


def _generate_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(96)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


@router.get("/debug-config")
async def debug_config() -> dict:
    """Shows the exact values the backend is using — open this in your browser to diagnose auth issues."""
    return {
        "spotify_client_id": settings.spotify_client_id or "⚠️  NOT SET",
        "spotify_redirect_uri": settings.spotify_redirect_uri,
        "frontend_url": settings.frontend_url,
        "client_id_length": len(settings.spotify_client_id),
    }


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    verifier, challenge = _generate_pkce()
    state = secrets.token_urlsafe(16)

    request.session["pkce_verifier"] = verifier
    request.session["oauth_state"] = state

    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
        "state": state,
        "scope": settings.spotify_scopes,
    }
    return RedirectResponse(f"https://accounts.spotify.com/authorize?{urlencode(params)}")


@router.post("/callback")
async def callback(
    body: CallbackBody,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Called by the frontend after Spotify redirects to the frontend /callback page.
    The frontend picks up ?code=...&state=... from the URL and POSTs them here.
    """
    stored_state = request.session.pop("oauth_state", None)
    if body.state != stored_state:
        raise HTTPException(status_code=400, detail="State mismatch")

    verifier = request.session.pop("pkce_verifier", None)
    if not verifier:
        raise HTTPException(status_code=400, detail="Missing PKCE verifier")

    try:
        token_data = await spotify_client.exchange_code_for_tokens(body.code, verifier)
    except Exception:
        raise HTTPException(status_code=400, detail="Token exchange failed")

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token", "")
    expires_at = int(time.time()) + token_data.get("expires_in", 3600)

    me = await spotify_client.get_current_spotify_user(access_token)
    spotify_id = me["id"]
    display_name = me.get("display_name")

    result = await db.execute(select(UserProfile).where(UserProfile.spotify_id == spotify_id))
    user = result.scalar_one_or_none()

    if not user:
        user = UserProfile(
            spotify_id=spotify_id,
            display_name=display_name,
            genre_profile={},
            top_artists={},
        )
        db.add(user)
        await db.flush()
    else:
        user.display_name = display_name

    await db.commit()
    await db.refresh(user)

    request.session["access_token"] = access_token
    request.session["refresh_token"] = refresh_token
    request.session["expires_at"] = expires_at
    request.session["user_id"] = user.id
    request.session["spotify_id"] = spotify_id

    return {"status": "ok"}


@router.get("/me", response_model=UserMeResponse)
async def me(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserMeResponse:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Auto-refresh token if near expiry
    expires_at = request.session.get("expires_at", 0)
    if int(time.time()) >= expires_at - 60:
        refresh_token = request.session.get("refresh_token")
        if refresh_token:
            try:
                token_data = await spotify_client.refresh_access_token(refresh_token)
                request.session["access_token"] = token_data["access_token"]
                request.session["expires_at"] = int(time.time()) + token_data.get("expires_in", 3600)
                if "refresh_token" in token_data:
                    request.session["refresh_token"] = token_data["refresh_token"]
            except Exception:
                pass  # Continue with potentially expired token

    result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return UserMeResponse(
        spotify_id=user.spotify_id,
        display_name=user.display_name,
        refreshed_at=user.refreshed_at,
        top_artists=user.top_artists or {},
        genre_profile=user.genre_profile or {},
    )


@router.post("/logout")
async def logout(request: Request) -> dict:
    request.session.clear()
    return {"status": "logged out"}


@router.post("/refresh")
async def refresh(request: Request) -> dict:
    refresh_token = request.session.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        token_data = await spotify_client.refresh_access_token(refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token refresh failed")

    request.session["access_token"] = token_data["access_token"]
    request.session["expires_at"] = int(time.time()) + token_data.get("expires_in", 3600)
    if "refresh_token" in token_data:
        request.session["refresh_token"] = token_data["refresh_token"]

    return {"status": "refreshed"}
