import hashlib
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.config import settings
from src.database import get_db
from src.database.models.user import User
from src.exceptions.auth import InvalidUIDError, UIDMissingError
from sqlalchemy.orm import Session
from sqlalchemy import select


# UID format: 64 hex characters
UID_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# Default debug UID (SHA256 of "debug" string)
DEBUG_UID = hashlib.sha256(b"debug").hexdigest()


def validate_uid(uid: str) -> bool:
    """Validate UID format (64 hex characters)."""
    return bool(UID_PATTERN.match(uid))


def get_or_create_user(db: Session, uid: str) -> User:
    """Get existing user or create new one with given UID."""
    stmt = select(User).where(User.uid == uid)
    user = db.execute(stmt).scalar_one_or_none()
    if user:
        return user

    # Create new user
    user = User(uid=uid)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_id(request: Request) -> int:
    """Get user_id from request state. Raises UIDMissingError if not found."""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise UIDMissingError()
    return user_id


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle UID-based authentication."""

    # Paths that don't require authentication
    EXCLUDED_PATHS = ["/", "/docs", "/openapi.json", "/redoc", "/auth"]

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for excluded paths (exact match or starts with for /auth)
        path = request.url.path
        if (
            path in self.EXCLUDED_PATHS
            or path.startswith("/auth/")
            or path.startswith("/videos/")
        ):
            return await call_next(request)

        # Get UID from header
        uid = request.headers.get("X-User-UID")

        # In debug mode, use default UID if not provided
        if not uid:
            if settings.DEBUG:
                uid = DEBUG_UID
            else:
                raise UIDMissingError()

        # Validate UID format
        if not validate_uid(uid):
            raise InvalidUIDError(uid)

        # Get or create user
        db = next(get_db())
        try:
            user = get_or_create_user(db, uid)
            # Inject user_id into request state
            request.state.user_id = user.id
        finally:
            db.close()

        return await call_next(request)
