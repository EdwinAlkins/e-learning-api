from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.models.user import User
from src.database.schemas.auth import UIDUser


def create_user(db: Session, user: UIDUser) -> User:
    """
    Create a new user in the database.

    Args:
        db: Database session
        user: User data to create

    Returns:
        User: The created user
    """
    db_user = User(uid=user.uid)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> User | None:
    """
    Get a user by their ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Optional[User]: The found user or None
    """
    return db.get(User, user_id)


def get_user_by_uid(db: Session, uid: str) -> User | None:
    """Get a user by their UID."""
    stmt = select(User).where(User.uid == uid)
    return db.execute(stmt).scalar_one_or_none()


def get_or_create_user(db: Session, uid: str) -> User:
    """Get existing user or create new one with given UID."""
    user = get_user_by_uid(db, uid)
    if not user:
        user = create_user(db, UIDUser(uid=uid))

    return user


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """
    Get a list of users with pagination.

    Args:
        db: Database session
        skip: Number of users to ignore (for pagination)
        limit: Maximum number of users to return

    Returns:
        List[User]: List of users
    """
    stmt = select(User).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def delete_user(db: Session, user_id: int) -> bool:
    """
    Delete a user.

    Args:
        db: Database session
        user_id: User ID to delete

    Returns:
        bool: True if the user has been deleted, False otherwise
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return False

    db.delete(db_user)
    db.commit()
    return True


def user_exists(db: Session, uid: str) -> bool:
    """
    Check if a user exists by their email.

    Args:
        db: Database session
        email: Email to check

    Returns:
        bool: True if the user exists, False otherwise
    """
    return get_user_by_uid(db, uid) is not None
