from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.models.note import Note


def get_notes(db: Session, user_id: int, video_id: str) -> list[Note]:
    """
    Get all notes for a user and video.

    Args:
        db: Database session
        user_id: User ID
        video_id: Video ID

    Returns:
        List[Note]: List of notes
    """
    stmt = (
        select(Note)
        .where(Note.user_id == user_id, Note.video_id == video_id)
        .order_by(Note.timecode)
    )
    return list(db.execute(stmt).scalars().all())


def create_note(
    db: Session, user_id: int, video_id: str, timecode: float, content: str
) -> Note:
    """
    Create a new note.

    Args:
        db: Database session
        user_id: User ID
        video_id: Video ID
        timecode: Timecode in seconds
        content: Note content

    Returns:
        Note: The created note
    """
    note = Note(user_id=user_id, video_id=video_id, timecode=timecode, content=content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_note(db: Session, note_id: int) -> Note | None:
    """
    Get a note by ID.

    Args:
        db: Database session
        note_id: Note ID

    Returns:
        Optional[Note]: The note or None
    """
    return db.get(Note, note_id)


def update_note(db: Session, note_id: int, user_id: int, content: str) -> Note | None:
    """
    Update a note, verifying ownership.

    Args:
        db: Database session
        note_id: Note ID
        user_id: User ID (for ownership verification)
        content: New content for the note

    Returns:
        Optional[Note]: The updated note or None if not found or not owned by user
    """
    note = get_note(db, note_id)
    if not note or note.user_id != user_id:
        return None

    note.content = content
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note_id: int, user_id: int) -> bool:
    """
    Delete a note, verifying ownership.

    Args:
        db: Database session
        note_id: Note ID
        user_id: User ID (for ownership verification)

    Returns:
        bool: True if deleted, False if not found or not owned by user
    """
    note = get_note(db, note_id)
    if not note or note.user_id != user_id:
        return False

    db.delete(note)
    db.commit()
    return True
