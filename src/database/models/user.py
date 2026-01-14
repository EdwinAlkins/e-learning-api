import datetime
import sqlalchemy.orm as so
import sqlalchemy as sa

from src.database import BaseModel


class User(BaseModel):
    __tablename__ = "user"

    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    uid: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, index=True)
    created_at: so.Mapped[datetime.datetime] = so.mapped_column(
        sa.DateTime, default=datetime.datetime.utcnow
    )
