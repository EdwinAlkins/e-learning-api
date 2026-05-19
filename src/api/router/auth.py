import secrets
import logging
import fastapi
import sqlalchemy.orm as so
from fastapi import HTTPException
from starlette.responses import Response

import src.database
import src.database.schemas.auth
from src.database import get_db
from src.crud.user import create_user, get_user_by_uid

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(prefix="/auth", tags=["auth"])


@router.post("/generate", response_model=src.database.schemas.auth.UIDResponse)
async def generate_uid(
    response: Response,
    db: so.Session = fastapi.Depends(get_db),
) -> src.database.schemas.auth.UIDResponse:
    """
    Generate a new anonymous UID and create a user.

    Returns:
        UIDResponse: The generated UID (64 hex characters)
    """
    # Generate 32 random bytes = 64 hex characters
    uid = secrets.token_hex(32)

    user = create_user(db, src.database.schemas.auth.UIDUser(uid=uid))
    # response.set_cookie(
    #     key="user_uid",
    #     value=uid,
    #     # httponly=True,  # Sécurité : empêche le JS côté client (ex: une extension malveillante) de lire le cookie
    #     # secure=False,   # IMPORTANT : Mets à True en production (quand tu seras en HTTPS)
    #     # samesite="lax", # Permet au cookie d'être envoyé depuis ton domaine
    #     # max_age=31536000 # Durée de vie d'un an en secondes
    # )
    return src.database.schemas.auth.UIDResponse(uid=user.uid)


@router.post("/restore", response_model=src.database.schemas.auth.UIDResponse)
async def restore_cookie(
    data: src.database.schemas.auth.UIDUser,
    response: Response,
    db: so.Session = fastapi.Depends(get_db),
) -> src.database.schemas.auth.UIDResponse:
    """
    Restore the cookie from the user_uid.
    """
    user = get_user_by_uid(db, data.uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # response.set_cookie(
    #     key="user_uid",
    #     value=user.uid,
    #     # httponly=True,  # Sécurité : empêche le JS côté client (ex: une extension malveillante) de lire le cookie
    #     # secure=False,   # IMPORTANT : Mets à True en production (quand tu seras en HTTPS)
    #     # samesite="lax", # Permet au cookie d'être envoyé depuis ton domaine
    #     # max_age=31536000 # Durée de vie d'un an en secondes
    # )
    logger.info(f"Restored cookie for user {user.uid}")
    return src.database.schemas.auth.UIDResponse(uid=user.uid)
