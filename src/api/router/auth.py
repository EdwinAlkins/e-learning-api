import secrets
import fastapi
import sqlalchemy.orm as so

import src.database
import src.database.schemas.auth
import src.database.models.user
from src.database import get_db
from sqlalchemy import select


router = fastapi.APIRouter(prefix="/auth", tags=["auth"])


@router.post("/generate", response_model=src.database.schemas.auth.UIDResponse)
async def generate_uid(
    db: so.Session = fastapi.Depends(get_db),
) -> src.database.schemas.auth.UIDResponse:
    """
    Generate a new anonymous UID and create a user.

    Returns:
        UIDResponse: The generated UID (64 hex characters)
    """
    # Generate 32 random bytes = 64 hex characters
    uid = secrets.token_hex(32)

    # Create user with this UID
    user = src.database.models.user.User(uid=uid)
    db.add(user)
    db.commit()
    db.refresh(user)

    return src.database.schemas.auth.UIDResponse(uid=uid)
