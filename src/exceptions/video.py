from fastapi import HTTPException


class VideoNotFoundError(HTTPException):
    def __init__(self, video_id: str):
        super().__init__(status_code=404, detail=f"Video {video_id} not found")


class NoteNotFoundError(HTTPException):
    def __init__(self, note_id: int):
        super().__init__(status_code=404, detail=f"Note {note_id} not found")
