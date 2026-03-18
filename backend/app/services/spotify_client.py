from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()

_SPOTIFY_API_BASE = "https://api.spotify.com/v1"
_SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

# In-memory token cache for client credentials
_cc_token: str | None = None
_cc_token_expires_at: float = 0.0

_semaphore = asyncio.Semaphore(5)


async def _get_client_credentials_token(force_refresh: bool = False) -> str:
    global _cc_token, _cc_token_expires_at

    if not force_refresh and _cc_token and time.time() < _cc_token_expires_at - 30:
        return _cc_token

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _SPOTIFY_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
        )
        response.raise_for_status()
        data = response.json()
        _cc_token = data["access_token"]
        _cc_token_expires_at = time.time() + data["expires_in"]
        return _cc_token


async def _request_with_backoff(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs: Any,
) -> httpx.Response:
    for attempt in range(4):
        async with _semaphore:
            response = await client.request(method, url, **kwargs)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
            await asyncio.sleep(retry_after)
            continue

        response.raise_for_status()
        return response

    response.raise_for_status()
    return response


async def get_artists_batch(ids: list[str], access_token: str | None = None) -> list[dict]:
    """Fetch up to 50 artists per call using batch endpoint."""
    results: list[dict] = []

    for i in range(0, len(ids), 50):
        chunk = ids[i : i + 50]
        # Refresh token per batch to avoid expiry after long search phase
        token = access_token or await _get_client_credentials_token(force_refresh=(i > 0))
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient(base_url=_SPOTIFY_API_BASE) as client:
                response = await _request_with_backoff(
                    client, "GET", "/artists", headers=headers, params={"ids": ",".join(chunk)}
                )
                results.extend(response.json().get("artists") or [])
        except Exception:
            # On failure, retry with a fresh token once
            try:
                token = await _get_client_credentials_token(force_refresh=True)
                headers = {"Authorization": f"Bearer {token}"}
                async with httpx.AsyncClient(base_url=_SPOTIFY_API_BASE) as client:
                    response = await _request_with_backoff(
                        client, "GET", "/artists", headers=headers, params={"ids": ",".join(chunk)}
                    )
                    results.extend(response.json().get("artists") or [])
            except Exception:
                pass  # Skip batch on persistent failure

    return [a for a in results if a]


async def get_related_artists(artist_id: str, access_token: str | None = None) -> list[dict]:
    """Spotify deprecated this endpoint in Nov 2024 — always returns empty."""
    return []


async def search_artist(name: str, access_token: str | None = None) -> dict | None:
    token = access_token or await _get_client_credentials_token()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(base_url=_SPOTIFY_API_BASE) as client:
            response = await _request_with_backoff(
                client,
                "GET",
                "/search",
                headers=headers,
                params={"q": name, "type": "artist", "limit": 1},
            )
            items = response.json().get("artists", {}).get("items", [])
            return items[0] if items else None
    except Exception:
        return None


_LASTFM_API_BASE = "https://ws.audioscrobbler.com/2.0/"


async def get_lastfm_genres(artist_name: str) -> list[str]:
    """Fetch top genre tags for an artist from Last.fm."""
    api_key = settings.lastfm_api_key
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                _LASTFM_API_BASE,
                params={
                    "method": "artist.gettoptags",
                    "artist": artist_name,
                    "api_key": api_key,
                    "format": "json",
                    "autocorrect": 1,
                },
            )
            if response.status_code != 200:
                return []
            data = response.json()
            tags = data.get("toptags", {}).get("tag", [])
            # Filter out non-genre tags and return top 5
            skip = {"seen live", "favourite", "favorites", "love", "owned", "wishlist", "albums i own"}
            genres = [
                t["name"].lower()
                for t in tags
                if isinstance(t, dict) and t.get("name", "").lower() not in skip
            ]
            return genres[:5]
    except Exception:
        return []


async def get_top_artists(time_range: str, access_token: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(base_url=_SPOTIFY_API_BASE) as client:
        response = await _request_with_backoff(
            client,
            "GET",
            "/me/top/artists",
            headers=headers,
            params={"time_range": time_range, "limit": 50},
        )
        return response.json().get("items", [])


async def get_current_spotify_user(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(base_url=_SPOTIFY_API_BASE) as client:
        response = await _request_with_backoff(client, "GET", "/me", headers=headers)
        return response.json()


async def exchange_code_for_tokens(code: str, code_verifier: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
                "client_id": settings.spotify_client_id,
                "code_verifier": code_verifier,
            },
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.spotify_client_id,
            },
        )
        response.raise_for_status()
        return response.json()
