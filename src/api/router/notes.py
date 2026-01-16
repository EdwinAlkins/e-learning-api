import fastapi
import sqlalchemy.orm as so
from starlette.requests import Request

import src.database
import src.database.schemas.note
import src.crud.note
from src.database import get_db
from src.services.catalog import catalog_service
from src.exceptions.video import VideoNotFoundError, NoteNotFoundError
from src.api.middleware.auth import get_user_id


router = fastapi.APIRouter(prefix="/notes", tags=["notes"])


@router.get("/{video_id}", response_model=list[src.database.schemas.note.NoteResponse])
async def get_notes(
    video_id: str,
    request: Request,
    db: so.Session = fastapi.Depends(get_db),
) -> list[src.database.schemas.note.NoteResponse]:
    """
    Get all notes for a video.

    Args:
        video_id: Video ID
        request: Request object (contains user_id from middleware)
        db: Database session

    Returns:
        List[NoteResponse]: List of notes for the video
    """
    # Verify video exists
    if not catalog_service.video_exists(video_id):
        raise VideoNotFoundError(video_id)

    user_id = get_user_id(request)
    notes = src.crud.note.get_notes(db, user_id, video_id)

    return [
        src.database.schemas.note.NoteResponse(
            id=note.id,
            video_id=note.video_id,
            timecode=note.timecode,
            content=note.content,
            created_at=note.created_at,
        )
        for note in notes
    ]


@router.post("/{video_id}", response_model=src.database.schemas.note.NoteResponse)
async def create_note(
    video_id: str,
    note_create: src.database.schemas.note.NoteCreate,
    request: Request,
    db: so.Session = fastapi.Depends(get_db),
) -> src.database.schemas.note.NoteResponse:
    """
    Create a note for a video.

    Args:
        video_id: Video ID
        note_create: Note creation data
        request: Request object (contains user_id from middleware)
        db: Database session

    Returns:
        NoteResponse: The created note
    """
    # Verify video exists
    if not catalog_service.video_exists(video_id):
        raise VideoNotFoundError(video_id)

    user_id = get_user_id(request)
    note = src.crud.note.create_note(
        db, user_id, video_id, note_create.timecode, note_create.content
    )

    return src.database.schemas.note.NoteResponse(
        id=note.id,
        video_id=note.video_id,
        timecode=note.timecode,
        content=note.content,
        created_at=note.created_at,
    )


@router.put("/{note_id}", response_model=src.database.schemas.note.NoteResponse)
async def update_note(
    note_id: int,
    note_update: src.database.schemas.note.NoteUpdate,
    request: Request,
    db: so.Session = fastapi.Depends(get_db),
) -> src.database.schemas.note.NoteResponse:
    """
    Update a note.

    Args:
        note_id: Note ID
        note_update: Note update data
        request: Request object (contains user_id from middleware)
        db: Database session

    Returns:
        NoteResponse: The updated note

    Raises:
        NoteNotFoundError: If note not found or not owned by user
    """
    user_id = get_user_id(request)
    note = src.crud.note.update_note(db, note_id, user_id, note_update.content)

    if not note:
        raise NoteNotFoundError(note_id)

    return src.database.schemas.note.NoteResponse(
        id=note.id,
        video_id=note.video_id,
        timecode=note.timecode,
        content=note.content,
        created_at=note.created_at,
    )


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    request: Request,
    db: so.Session = fastapi.Depends(get_db),
):
    """
    Delete a note.

    Args:
        note_id: Note ID
        request: Request object (contains user_id from middleware)
        db: Database session

    Raises:
        NoteNotFoundError: If note not found or not owned by user
    """
    user_id = get_user_id(request)
    deleted = src.crud.note.delete_note(db, note_id, user_id)

    if not deleted:
        raise NoteNotFoundError(note_id)
