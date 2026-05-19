import hashlib
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.config import settings
from src.database import get_db
from src.exceptions.auth import InvalidUIDError, UIDMissingError
from src.crud.user import get_or_create_user


# UID format: 64 hex characters
UID_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# Default debug UID (SHA256 of "debug" string)
DEBUG_UID = hashlib.sha256(b"debug").hexdigest()


def validate_uid(uid: str) -> bool:
    """Validate UID format (64 hex characters)."""
    return bool(UID_PATTERN.match(uid))


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
            or path.startswith("/auth")
            or path.startswith("/videos")
        ):
            return await call_next(request)

        # Get UID from header
        uid = request.headers.get("X-User-UID")

        # if uid is not found, try to get it from cookies
        if not uid:
            uid = request.cookies.get("user_uid")
        elif not uid and request.query_params.get("user_uid"):
            uid = request.query_params.get("user_uid")
        elif (
            not uid and settings.DEBUG
        ):  # In debug mode, use default UID if not provided
            uid = DEBUG_UID
        elif not uid:  # If uid is still not found, raise an error
            raise UIDMissingError()

        # Validate UID format
        if not validate_uid(uid):
            raise InvalidUIDError(uid)

        # Get or create user and inject user_id into request state
        db = next(get_db())
        try:
            user = get_or_create_user(db, uid)
            # Inject user_id into request state
            request.state.user_id = user.id
        finally:
            db.close()

        return await call_next(request)
