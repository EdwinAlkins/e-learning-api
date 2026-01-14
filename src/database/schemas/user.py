import pydantic
from pydantic import Field

EmailField = Field(
    min_length=1,
    max_length=100,
    description="The email of the user",
    json_schema_extra={"example": "john.doe@example.com"},
)
NameField = Field(
    min_length=1,
    max_length=100,
    description="The name of the user",
    json_schema_extra={"example": "John Doe"},
)
UidField = Field(description="The ID of the user", json_schema_extra={"example": 1})


class UserBase(pydantic.BaseModel):
    email: str = EmailField
    name: str = NameField


class User(UserBase):
    uid: int

    model_config = pydantic.ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    pass


class UserUpdate(pydantic.BaseModel):
    email: str | None = EmailField
    name: str | None = NameField
