import logging
import src.config

logging.basicConfig(level=logging.getLevelName(src.config.settings.LOG_LEVEL))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(debug=src.config.settings.DEBUG, openapi_tags=tags_metadata)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware (must be after CORS)
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(formations.router)
app.include_router(videos.router)
app.include_router(progress.router)
app.include_router(notes.router)


@app.on_event("startup")
async def startup_event():
    """Initialize catalog service on startup."""
    logger.info("Initializing catalog service...")
    catalog_service.refresh()


@app.get("/", status_code=200)
def healthcheck():
    return {"message": "health ok"}
