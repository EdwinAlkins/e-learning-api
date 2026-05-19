import pydantic


class UIDUser(pydantic.BaseModel):
    uid: str

    model_config = pydantic.ConfigDict(
        json_schema_extra={"example": {"uid": "a1b2c3d4e5f6..."}},
        from_attributes=True,
    )


class UIDResponse(UIDUser):
    pass
