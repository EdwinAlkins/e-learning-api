import asyncio
import logging
import src.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.middleware.auth import AuthMiddleware
from src.api.router import auth, formations, videos, progress, notes
from src.services.catalog import catalog_service

logger = logging.getLogger(__name__)

tags_metadata = [
    {
        "name": "auth",
        "description": "Authentication and UID generation",
    },
    {
        "name": "formations",
        "description": "Formation catalog",
    },
    {
        "name": "videos",
        "description": "Video streaming",
    },
    {
        "name": "progress",
        "description": "User progress tracking",
    },
    {
        "name": "notes",
        "description": "User notes",
    },
]


def refresh_catalog_background():
    """Background task to refresh the catalog by scanning videos."""
    logger.info("Starting background catalog refresh...")
    try:
        catalog_service.refresh()
        logger.info("Background catalog refresh completed")
    except Exception as e:
        logger.error(f"Error during background catalog refresh: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Initializing catalog service...")
    # Load catalog from cache if available
    catalog_service.get_catalog()
    # Schedule background refresh to update catalog and cache
    background_task = asyncio.create_task(asyncio.to_thread(refresh_catalog_background))
    # Keep reference to prevent garbage collection
    app.state.background_task = background_task
    yield
    # Shutdown (if needed in the future)


app = FastAPI(
    debug=src.config.settings.DEBUG,
    title="FastAPI Database Template",
    description="FastAPI Database Template",
    version="0.1.0",
    docs_url="/docs" if src.config.settings.DEBUG else None,
    redoc_url="/redoc" if src.config.settings.DEBUG else None,
    openapi_url="/openapi.json" if src.config.settings.DEBUG else None,
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)
Instrumentator().instrument(app).expose(app)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=src.config.settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "x-user-uid"],
)

# Auth middleware (must be after CORS)
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(formations.router)
app.include_router(videos.router)
app.include_router(progress.router)
app.include_router(notes.router)


@app.get("/", status_code=200)
@app.head("/", status_code=200)
def healthcheck():
    return {"message": "health ok"}
