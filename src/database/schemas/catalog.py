import pydantic


class Video(pydantic.BaseModel):
    id: str
    title: str
    path: str
    duration: float

    model_config = pydantic.ConfigDict(from_attributes=True)


class Chapter(pydantic.BaseModel):
    name: str
    videos: list[Video]

    model_config = pydantic.ConfigDict(from_attributes=True)


class Formation(pydantic.BaseModel):
    name: str
    chapters: list[Chapter]

    model_config = pydantic.ConfigDict(from_attributes=True)


class CatalogResponse(pydantic.BaseModel):
    formations: list[Formation]

    model_config = pydantic.ConfigDict(from_attributes=True)
