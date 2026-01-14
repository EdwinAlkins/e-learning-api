from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.models.user import User
from src.database.schemas.user import UserCreate, UserUpdate
from src.exceptions.user import UserNotFoundError


def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user in the database.

    Args:
        db: Database session
        user: User data to create

    Returns:
        User: The created user
    """
    db_user = User(email=user.email, name=user.name)
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


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Get a user by their email.

    Args:
        db: Database session
        email: User email

    Returns:
        Optional[User]: The found user or None
    """
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


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


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
    """
    Update a user.

    Args:
        db: Database session
        user_id: User ID to update
        user_update: Update data

    Returns:
        User: The updated user

    Raises:
        UserNotFoundError: If the user is not found
    """
    db_user = get_user(db, user_id)
    if not db_user:
        raise UserNotFoundError(user_id)

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


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


def search_users_by_name(
    db: Session, name: str, skip: int = 0, limit: int = 100
) -> list[User]:
    """
    Search users by name (partial search).

    Args:
        db: Database session
        name: Name to search
        skip: Number of users to ignore (for pagination)
        limit: Maximum number of users to return

    Returns:
        List[User]: List of matching users
    """
    stmt = select(User).where(User.name.ilike(f"%{name}%")).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def user_exists(db: Session, email: str) -> bool:
    """
    Check if a user exists by their email.

    Args:
        db: Database session
        email: Email to check

    Returns:
        bool: True if the user exists, False otherwise
    """
    return get_user_by_email(db, email) is not None
