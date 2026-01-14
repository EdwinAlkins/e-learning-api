import datetime
import sqlalchemy.orm as so
import sqlalchemy as sa

from src.database import BaseModel
from src.database.models.user import User


class Note(BaseModel):
    __tablename__ = "note"

    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    video_id: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    timecode: so.Mapped[float] = so.mapped_column(sa.Float)
    content: so.Mapped[str] = so.mapped_column(sa.Text)
    created_at: so.Mapped[datetime.datetime] = so.mapped_column(
        sa.DateTime, default=datetime.datetime.utcnow
    )

    user: so.Mapped[User] = so.relationship("User")
