import pydantic


class ProgressResponse(pydantic.BaseModel):
    last_position: float

    model_config = pydantic.ConfigDict(from_attributes=True)


class ProgressUpdate(pydantic.BaseModel):
    last_position: float

    model_config = pydantic.ConfigDict(
        json_schema_extra={"example": {"last_position": 123.45}}
    )


class VideoProgress(pydantic.BaseModel):
    id: str
    title: str
    progress_percentage: float

    model_config = pydantic.ConfigDict(from_attributes=True)


class ChapterProgress(pydantic.BaseModel):
    name: str
    videos: list[VideoProgress]
    progress_percentage: float

    model_config = pydantic.ConfigDict(from_attributes=True)


class FormationProgress(pydantic.BaseModel):
    name: str
    chapters: list[ChapterProgress]
    progress_percentage: float

    model_config = pydantic.ConfigDict(from_attributes=True)
