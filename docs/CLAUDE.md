# Roskilde Music Matcher

Spotify-powered recommendation engine for Roskilde Festival 2026. Matches users' listening history against the festival lineup.

Read `docs/architecture.docx` for full architecture, data model, matching algorithm, and API design before starting any work.

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async + asyncpg), Alembic, httpx, BeautifulSoup4, thefuzz
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, recharts, TanStack Query
- **Database**: PostgreSQL 16 (JSONB for genre data)
- **Dev**: Docker Compose

## Commands

```bash
# Start all services
docker compose up -d

# Run backend (dev)
cd backend && uvicorn app.main:app --reload --port 8000

# Run migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"

# Seed festival artists (scrape + enrich from Spotify)
cd backend && python -m app.services.enrichment

# Run backend tests
cd backend && pytest

# Run frontend (dev)
cd frontend && npm run dev

# Type check frontend
cd frontend && npx tsc --noEmit
```

## Project Layout

```
backend/app/
  main.py              # FastAPI app entry point
  config.py            # pydantic-settings
  database.py          # async SQLAlchemy engine + session
  models/              # SQLAlchemy models (artist, user, recommendation)
  routers/             # FastAPI routers (auth, artists, recommendations, schedule)
  services/            # Business logic (spotify_client, scraper, enrichment, matching_engine, genre_analyzer)
  schemas/             # Pydantic response models

frontend/src/
  pages/               # Landing, Dashboard, ArtistDetail, Schedule
  components/          # ArtistCard, GenreRadar, ScoreBadge, ScheduleTimeline, GenreTag, SpotifyEmbed
  hooks/               # useSpotifyAuth, useRecommendations, useSchedule
  api/client.ts        # Fetch wrapper
  types/index.ts       # TypeScript interfaces
```

## Coding Conventions

### Backend (Python)
- Async everywhere: async routes, async SQLAlchemy sessions, async httpx calls
- Pydantic models for all request/response schemas (in `schemas/`, not `models/`)
- SQLAlchemy models in `models/`, business logic in `services/`, HTTP layer in `routers/`
- Use `httpx.AsyncClient` for all external API calls
- Type hints on all function signatures
- Use `from __future__ import annotations` in all files

### Frontend (TypeScript)
- Functional components only
- TanStack Query for all server state — no useState for API data
- Tailwind only — no CSS files, no styled-components
- Mobile-first: design for small screens, scale up

### Database
- Genre data is JSONB arrays — do not normalize into junction tables
- All timestamps use TIMESTAMPTZ

## Key Gotchas

- **Spotify genres live on artists, not tracks.** No per-track genre API exists.
- **Spotify micro-genres are hyper-specific** ("stockholm indie", "german techno"). genre_analyzer must do fuzzy matching — see architecture doc Section 5.2 for the three-level strategy.
- **Spotify dev mode = 25 users max.** Production needs a quota extension request.
- **Artist name mismatches** (e.g., "¥ØU$UK€ ¥UK1MAT$U") — use `data/lineup_fallback.json` for manual Spotify ID overrides.
- **Rate limits**: ~180 req/min per Spotify token. Use batch `/v1/artists?ids=...` (50/call). Cache aggressively.

## Environment

Copy `.env.example` → `.env`. Required: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`, `DATABASE_URL`, `SECRET_KEY`.

## Implementation Order

Follow phases in the architecture doc (Section 11). Start with Phase 1: Docker Compose + FastAPI scaffold + scraper + enrichment pipeline. Each phase should be a working increment.
