from fastapi import HTTPException


class UserNotFoundError(HTTPException):
    def __init__(self, user_id: int):
        super().__init__(status_code=404, detail=f"User {user_id} not found")


class UserAlreadyExistsError(HTTPException):
    def __init__(self, email: str, name: str):
        super().__init__(
            status_code=400,
            detail=f"User with email {email} or name {name} already exists",
        )
