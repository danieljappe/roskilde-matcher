from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://roskilde:roskilde@localhost:5432/roskilde"
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "https://localhost:5173/callback"
    secret_key: str = "dev-secret-key-change-in-production"
    frontend_url: str = "https://localhost:5173"
    spotify_scopes: str = "user-top-read"
    lastfm_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
