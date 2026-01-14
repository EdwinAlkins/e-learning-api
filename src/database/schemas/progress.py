import pydantic


class ProgressResponse(pydantic.BaseModel):
    last_position: float

    model_config = pydantic.ConfigDict(from_attributes=True)


class ProgressUpdate(pydantic.BaseModel):
    last_position: float

    model_config = pydantic.ConfigDict(
        json_schema_extra={"example": {"last_position": 123.45}}
    )
