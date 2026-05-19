import sqlalchemy.orm as so
import sqlalchemy as sa

from src.database import BaseModel


class Video(BaseModel):
    __tablename__ = "video"

    id: so.Mapped[str] = so.mapped_column(sa.String(64), primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(255), index=True)
    path: so.Mapped[str] = so.mapped_column(sa.String(255))
    duration: so.Mapped[float] = so.mapped_column(sa.Float)

    chapter_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("chapter.id"), index=True
    )
    chapter: so.Mapped["Chapter"] = so.relationship(back_populates="videos")


class Chapter(BaseModel):
    __tablename__ = "chapter"

    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(255), index=True)

    formation_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("formation.id"), index=True
    )
    formation: so.Mapped["Formation"] = so.relationship(back_populates="chapters")

    videos: so.Mapped[list[Video]] = so.relationship(Video, back_populates="chapter")


class Formation(BaseModel):
    __tablename__ = "formation"

    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(255), index=True)

    chapters: so.Mapped[list[Chapter]] = so.relationship(
        Chapter, back_populates="formation"
    )
