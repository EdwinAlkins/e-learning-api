import datetime
import pydantic


class NoteResponse(pydantic.BaseModel):
    id: int
    video_id: str
    timecode: float
    content: str
    created_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)


class NoteCreate(pydantic.BaseModel):
    timecode: float
    content: str

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "example": {"timecode": 321.5, "content": "Concept important"}
        }
    )


class NoteUpdate(pydantic.BaseModel):
    content: str

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "example": {"content": "Contenu mis à jour"}
        }
    )
