import sqlalchemy.orm as so

import src.database


class User(src.database.BaseModel):
    __tablename__ = "user"

    uid: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    email: so.Mapped[str] = so.mapped_column(unique=True, index=True)
    name: so.Mapped[str] = so.mapped_column(index=True)
