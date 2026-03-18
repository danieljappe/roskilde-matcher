from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.routers import artists, auth, recommendations

settings = get_settings()

app = FastAPI(title="RoskildeMatcher", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, https_only=False)

app.include_router(auth.router)
app.include_router(artists.router)
app.include_router(recommendations.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
