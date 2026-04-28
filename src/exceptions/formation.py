from fastapi import HTTPException


class FormationNotFoundError(HTTPException):
    def __init__(self, formation_name: str):
        super().__init__(status_code=404, detail=f"Formation {formation_name} not found")


class ChapterNotFoundError(HTTPException):
    def __init__(self, chapter_name: str):
        super().__init__(status_code=404, detail=f"Chapter {chapter_name} not found")
