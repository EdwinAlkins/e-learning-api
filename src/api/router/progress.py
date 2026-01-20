import fastapi
import sqlalchemy.orm as so
from starlette.requests import Request

import src.database
import src.database.schemas.progress
import src.crud.progress
from src.database import get_db
from src.services.catalog import catalog_service
from src.exceptions.video import VideoNotFoundError, FormationNotFoundError
from src.api.middleware.auth import get_user_id


router = fastapi.APIRouter(prefix="/progress", tags=["progress"])


@router.get(
    "/formation/{formation_name}",
    response_model=src.database.schemas.progress.FormationProgress,
)
async def get_formation_progress(
    formation_name: str,
    request: Request,
    db: so.Session = fastapi.Depends(get_db),
) -> src.database.schemas.progress.FormationProgress:
    """
    Get progress for a formation with percentages for videos, chapters, and the formation.

    Args:
        formation_name: Name of the formation
        request: Request object (contains user_id from middleware)
        db: Database session

    Returns:
        FormationProgress: The progress with percentages for videos, chapters, and formation
    """
    # Get formation from catalog
    formation = catalog_service.get_formation(formation_name)
    if not formation:
        raise FormationNotFoundError(formation_name)

    user_id = get_user_id(request)

    # Collect all video IDs from the formation
    all_video_ids: list[str] = []
    for chapter in formation.chapters:
        for video in chapter.videos:
            all_video_ids.append(video.id)

    # Get all progresses for these videos
    progresses_dict = src.crud.progress.get_progresses_for_videos(
        db, user_id, all_video_ids
    )

    # Build response with progress percentages
    chapter_progresses: list[src.database.schemas.progress.ChapterProgress] = []
    all_video_percentages: list[float] = []

    for chapter in formation.chapters:
        video_progresses: list[src.database.schemas.progress.VideoProgress] = []
        chapter_video_percentages: list[float] = []

        for video in chapter.videos:
            # Calculate progress percentage for this video
            progress = progresses_dict.get(video.id)
            if progress and video.duration > 0:
                percentage = min(
                    100.0, (progress.last_position / video.duration) * 100.0
                )
            else:
                percentage = 0.0

            video_progresses.append(
                src.database.schemas.progress.VideoProgress(
                    id=video.id,
                    title=video.title,
                    progress_percentage=percentage,
                )
            )
            chapter_video_percentages.append(percentage)
            all_video_percentages.append(percentage)

        # Calculate chapter progress (average of video percentages)
        chapter_progress_percentage = (
            sum(chapter_video_percentages) / len(chapter_video_percentages)
            if chapter_video_percentages
            else 0.0
        )

        chapter_progresses.append(
            src.database.schemas.progress.ChapterProgress(
                name=chapter.name,
                videos=video_progresses,
                progress_percentage=chapter_progress_percentage,
            )
        )

    # Calculate formation progress (average of all video percentages)
    formation_progress_percentage = (
        sum(all_video_percentages) / len(all_video_percentages)
        if all_video_percentages
        else 0.0
    )

    return src.database.schemas.progress.FormationProgress(
        name=formation.name,
        chapters=chapter_progresses,
        progress_percentage=formation_progress_percentage,
    )


@router.get(
    "/{video_id}", response_model=src.database.schemas.progress.ProgressResponse
)
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

    user_id = get_user_id(request)
    progress = src.crud.progress.get_progress(db, user_id, video_id)

    if not progress:
        # Return default position if no progress exists
        return src.database.schemas.progress.ProgressResponse(last_position=0.0)

    return src.database.schemas.progress.ProgressResponse(
        last_position=progress.last_position
    )


@router.post(
    "/{video_id}", response_model=src.database.schemas.progress.ProgressResponse
)
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

    user_id = get_user_id(request)
    progress = src.crud.progress.upsert_progress(
        db, user_id, video_id, progress_update.last_position
    )

    return src.database.schemas.progress.ProgressResponse(
        last_position=progress.last_position
    )
