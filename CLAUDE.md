# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (includes AI/transcription extras)
uv sync --group ai --group dev

# Run the API (development)
uv run fastapi dev src/api/fastapi_app.py
# OR
uv run -m src.api

# Run tests
uv run pytest
uv run pytest tests/unit/          # unit tests only
uv run pytest tests/integration/   # integration tests only
uv run pytest tests/unit/test_crud_user.py  # single file

# Lint and format
uv run ruff check .
uv run ruff format .
uv run ruff check --fix .

# Database migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head

# Utility scripts
uv run python -m src.scripts.convert_videos --help
uv run python -m src.scripts.transcribe --help
uv run python -m src.scripts.resume --help
```

## Architecture

FastAPI app served by Hypercorn. SQLite via SQLAlchemy (sync sessions). The package lives under `src/` and is installed as `e-learning-api`.

**Request flow:** HTTP → `AuthMiddleware` (validates/injects `user_id` from `X-User-UID` header) → router → CRUD/service layer.

**Key design decisions:**
- Authentication is UID-based (64 hex chars). `/auth/generate` creates a new anonymous user. Most routes require the header; `/`, `/auth/*`, and `/videos/*` are exempt.
- In `DEBUG=True` mode, a missing UID header falls back to a fixed debug UID (SHA256 of `"debug"`). The `/docs`, `/redoc`, and `/openapi.json` endpoints are also only exposed in debug mode.
- The video catalog is **file-system-driven**: `CatalogService` scans `VIDEOS_PATH` (structure: `formation/chapter/video.mp4`) and generates deterministic video IDs as `sha1(last 3 path components)`. The catalog is persisted to `catalog_cache.json` and rebuilt in a background thread on startup.
- Video summaries are `.md` files stored alongside the `.mp4` files (same directory, same stem). Two summary strategies exist: `openapi` (OpenAI-compatible endpoint, default) and `gemini` (via `npx @google/gemini-cli`), selected by `SUMMARY_STRATEGY` env var.
- Pydantic schemas (`src/database/schemas/`) are separate from SQLAlchemy models (`src/database/models/`).

**Layer map:**
- `src/api/router/` — FastAPI route handlers
- `src/api/middleware/` — auth middleware
- `src/crud/` — database read/write helpers (take `Session` as first arg)
- `src/services/` — business logic (`catalog.py`, `summary.py`, `transcription.py`)
- `src/database/models/` — SQLAlchemy ORM models
- `src/database/schemas/` — Pydantic request/response models
- `src/scripts/` — standalone CLI scripts (convert, transcribe, resume)

## Configuration

All settings in `src/config.py` via `pydantic-settings`. Loaded from `.env.template` then `.env` then environment variables.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_PATH` | `database.db` | SQLite file path |
| `VIDEOS_PATH` | `videos/` | Root directory for video files |
| `CATALOG_CACHE_PATH` | `catalog_cache.json` | Catalog JSON cache |
| `DEBUG` | `False` | Enables docs UI, fallback UID |
| `SUMMARY_STRATEGY` | `openapi` | `openapi` or `gemini` |
| `OPENAI_BASE_URL` | `http://localhost:1234/v1` | LLM endpoint (e.g. LM Studio) |
| `OPENAI_API_KEY` | `lm-studio` | API key for LLM |
| `OPENAI_MODEL` | `openapi/gpt-oss-20b` | Model name |

## Docker

```bash
docker build -f docker/Dockerfile -t formation-backend .
docker run -d -p 8000:8000 \
  -v $(pwd)/database.db:/app/data/database.db \
  -v $(pwd)/videos:/app/videos \
  -e DATABASE_PATH=/app/data/database.db \
  -e VIDEOS_PATH=/app/videos \
  formation-backend
```
