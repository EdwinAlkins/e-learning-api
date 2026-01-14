from fastapi import HTTPException


class InvalidUIDError(HTTPException):
    def __init__(self, uid: str | None = None):
        detail = "Invalid UID format" if uid is None else f"Invalid UID format: {uid}"
        super().__init__(status_code=400, detail=detail)


class UIDMissingError(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="X-User-UID header is required")
