import fastapi
import sqlalchemy.orm as so
from starlette.requests import Request

import src.database
import src.database.schemas.progress
import src.crud.progress
from src.database import get_db
from src.services.catalog import catalog_service
from src.exceptions.video import VideoNotFoundError


router = fastapi.APIRouter(prefix="/progress", tags=["progress"])


@router.get("/{video_id}", response_model=src.database.schemas.progress.ProgressResponse)
async def get_progress(
    video_id: str,
    request: Request,
    db: so.Session = fastapi.Depends(get_db),
) -> src.database.schemas.progress.ProgressResponse:
    """
    Get progress for a video.

    Args:
        video_id: Video ID
        request: Request object (contains user_id from middleware)
        db: Database session

    Returns:
        ProgressResponse: The progress with last_position
    """
    # Verify video exists
    if not catalog_service.video_exists(video_id):
        raise VideoNotFoundError(video_id)

    user_id = request.state.user_id
    progress = src.crud.progress.get_progress(db, user_id, video_id)

    if not progress:
        # Return default position if no progress exists
        return src.database.schemas.progress.ProgressResponse(last_position=0.0)

    return src.database.schemas.progress.ProgressResponse(
        last_position=progress.last_position
    )


@router.post("/{video_id}", response_model=src.database.schemas.progress.ProgressResponse)
async def update_progress(
    video_id: str,
    progress_update: src.database.schemas.progress.ProgressUpdate,
    request: Request,
    db: so.Session = fastapi.Depends(get_db),
) -> src.database.schemas.progress.ProgressResponse:
    """
    Update progress for a video.

    Args:
        video_id: Video ID
        progress_update: Progress update data
        request: Request object (contains user_id from middleware)
        db: Database session

    Returns:
        ProgressResponse: The updated progress
    """
    # Verify video exists
    if not catalog_service.video_exists(video_id):
        raise VideoNotFoundError(video_id)

    user_id = request.state.user_id
    progress = src.crud.progress.upsert_progress(
        db, user_id, video_id, progress_update.last_position
    )

    return src.database.schemas.progress.ProgressResponse(
        last_position=progress.last_position
    )
