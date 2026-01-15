from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.models.progress import Progress


def get_progress(db: Session, user_id: int, video_id: str) -> Progress | None:
    """
    Get progress for a user and video.

    Args:
        db: Database session
        user_id: User ID
        video_id: Video ID

    Returns:
        Optional[Progress]: The progress or None
    """
    stmt = select(Progress).where(
        Progress.user_id == user_id, Progress.video_id == video_id
    )
    return db.execute(stmt).scalar_one_or_none()


def get_progresses_for_videos(
    db: Session, user_id: int, video_ids: list[str]
) -> dict[str, Progress]:
    """
    Get progress for a user and multiple videos.

    Args:
        db: Database session
        user_id: User ID
        video_ids: List of video IDs

    Returns:
        dict[str, Progress]: Dictionary mapping video_id to Progress (or None if no progress)
    """
    if not video_ids:
        return {}

    stmt = select(Progress).where(
        Progress.user_id == user_id, Progress.video_id.in_(video_ids)
    )
    progresses = db.execute(stmt).scalars().all()
    return {progress.video_id: progress for progress in progresses}


def upsert_progress(
    db: Session, user_id: int, video_id: str, last_position: float
) -> Progress:
    """
    Create or update progress for a user and video.

    Args:
        db: Database session
        user_id: User ID
        video_id: Video ID
        last_position: Last position in seconds

    Returns:
        Progress: The created or updated progress
    """
    progress = get_progress(db, user_id, video_id)
    if progress:
        progress.last_position = last_position
    else:
        progress = Progress(
            user_id=user_id, video_id=video_id, last_position=last_position
        )
        db.add(progress)

    db.commit()
    db.refresh(progress)
    return progress
