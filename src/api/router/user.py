import fastapi
import sqlalchemy.orm as so

import src.database.models
import src.database.schemas.user
import src.crud.user
import src.exceptions.user


router = fastapi.APIRouter(prefix="/user", tags=["user"])


@router.get("/", response_model=list[src.database.schemas.user.User])
async def get_users(
    db: so.Session = fastapi.Depends(src.database.get_db),
    page: int = fastapi.Query(0, ge=0),
    size: int = fastapi.Query(10, ge=1, le=100),
) -> list[src.database.schemas.user.User]:
    return src.crud.user.get_users(db, page, size)


@router.get("/{user_id}", response_model=src.database.schemas.user.User)
async def get_user(
    user_id: int, db: so.Session = fastapi.Depends(src.database.get_db)
) -> src.database.schemas.user.User:
    user = src.crud.user.get_user(db, user_id)
    if not user:
        raise src.exceptions.user.UserNotFoundError(user_id)
    return user


@router.post("/", response_model=src.database.schemas.user.User)
async def create_user(
    user: src.database.schemas.user.UserCreate,
    db: so.Session = fastapi.Depends(src.database.get_db),
) -> src.database.schemas.user.User:
    if src.crud.user.get_user_by_email(
        db, user.email
    ) or src.crud.user.search_users_by_name(db, user.name):
        raise src.exceptions.user.UserAlreadyExistsError(user.email, user.name)
    return src.crud.user.create_user(db, user)


@router.put("/{user_id}", response_model=src.database.schemas.user.User)
async def update_user(
    user_id: int,
    user: src.database.schemas.user.UserUpdate,
    db: so.Session = fastapi.Depends(src.database.get_db),
) -> src.database.schemas.user.User:
    return src.crud.user.update_user(db, user_id, user)


@router.delete("/{user_id}", response_model=bool)
async def delete_user(
    user_id: int,
    db: so.Session = fastapi.Depends(src.database.get_db),
) -> bool:
    return src.crud.user.delete_user(db, user_id)
