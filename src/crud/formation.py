from pathlib import Path

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, delete as sql_delete

from src.database.models.formation import Formation, Chapter, Video
from src.database.schemas.catalog import (
    Formation as FormationSchema,
    Chapter as ChapterSchema,
    Video as VideoSchema,
    CatalogResponse,
)
from src.exceptions.formation import FormationNotFoundError, ChapterNotFoundError


def get_formations(db: Session) -> list[Formation]:
    stmt = select(Formation).options(
        selectinload(Formation.chapters).selectinload(Chapter.videos)
    )
    return list(db.scalars(stmt).all())


def get_formation(db: Session, formation_name: str) -> Formation | None:
    stmt = select(Formation).where(Formation.name == formation_name)
    return db.execute(stmt).scalar_one_or_none()


def add_formation(db: Session, formation: FormationSchema) -> Formation:
    db_formation = Formation(name=formation.name)
    db.add(db_formation)
    db.commit()
    db.refresh(db_formation)
    return db_formation


def add_chapter(db: Session, chapter: ChapterSchema, formation_name: str) -> Chapter:
    formation = get_formation(db, formation_name)
    if not formation:
        raise FormationNotFoundError(formation_name)
    db_chapter = Chapter(name=chapter.name, formation=formation)
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter


def get_chapter(db: Session, chapter_name: str) -> Chapter | None:
    stmt = select(Chapter).where(Chapter.name == chapter_name)
    return db.execute(stmt).scalar_one_or_none()


def add_video(db: Session, video: VideoSchema, chapter_name: str) -> Video:
    chapter = get_chapter(db, chapter_name)
    if not chapter:
        raise ChapterNotFoundError(chapter_name)
    db_video = Video(
        title=video.title, path=video.path, duration=video.duration, chapter=chapter
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video


def sync_catalog(db: Session, catalog: CatalogResponse, videos_path: Path) -> None:
    """Replace all catalog data in the DB with fresh scan results."""
    db.execute(sql_delete(Video))
    db.execute(sql_delete(Chapter))
    db.execute(sql_delete(Formation))
    db.flush()

    for formation in catalog.formations:
        f = Formation(name=formation.name)
        db.add(f)
        db.flush()
        for chapter in formation.chapters:
            c = Chapter(name=chapter.name, formation_id=f.id)
            db.add(c)
            db.flush()
            for video in chapter.videos:
                relative_path = str(Path(video.path).relative_to(videos_path))
                v = Video(
                    id=video.id,
                    title=video.title,
                    path=relative_path,
                    duration=video.duration,
                    chapter_id=c.id,
                )
                db.add(v)
    db.commit()
