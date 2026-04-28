import hashlib
import logging
from pathlib import Path

import ffmpeg

from src.config import settings
from src.database.schemas.catalog import CatalogResponse, Formation, Chapter, Video

logger = logging.getLogger(__name__)


class CatalogService:
    """Service for scanning and caching the video catalog from disk."""

    def __init__(self):
        self._catalog: CatalogResponse | None = None
        self._video_path_map: dict[str, Path] = {}

    def _get_videos_path(self) -> Path:
        videos_path = Path(settings.VIDEOS_PATH)
        if not videos_path.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            videos_path = project_root / videos_path
        return videos_path

    def _get_video_duration(self, video_path: Path) -> float:
        """Extract video duration using ffmpeg."""
        try:
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe["format"]["duration"])
            return duration
        except Exception as e:
            logger.warning(f"Failed to get duration for {video_path}: {e}")
            return 0.0

    def _keep_last_levels(self, video_path: Path, depth: int) -> Path:
        return Path(*video_path.parts[-depth:])

    def _generate_video_id(self, video_path: Path) -> str:
        truncated_path = str(self._keep_last_levels(video_path, 3))
        return hashlib.sha1(truncated_path.encode(), usedforsecurity=False).hexdigest()

    def _extract_title_from_filename(self, filename: str) -> str:
        """Extract title from filename, removing numeric prefix if present."""
        name = filename.replace(".mp4", "")
        parts = name.split(" - ", 1)
        if len(parts) == 2 and parts[0].strip().isdigit():
            return parts[1].strip()
        return name.strip()

    def _scan_directory(self, videos_path: Path) -> CatalogResponse:
        """Scan the videos directory and build catalog structure."""
        formations: list[Formation] = []

        if not videos_path.exists():
            logger.warning(f"Videos directory does not exist: {videos_path}")
            return CatalogResponse(formations=[])

        for formation_dir in sorted(videos_path.iterdir()):
            if not formation_dir.is_dir():
                continue

            chapters: list[Chapter] = []

            for chapter_dir in sorted(formation_dir.iterdir()):
                if not chapter_dir.is_dir():
                    continue

                videos: list[Video] = []

                for video_file in sorted(chapter_dir.glob("*.mp4")):
                    if not video_file.is_file():
                        continue

                    video_id = self._generate_video_id(video_file)
                    title = self._extract_title_from_filename(video_file.name)
                    duration = self._get_video_duration(video_file)

                    self._video_path_map[video_id] = video_file

                    videos.append(
                        Video(
                            id=video_id,
                            title=title,
                            path=str(video_file),
                            duration=duration,
                        )
                    )

                if videos:
                    chapters.append(Chapter(name=chapter_dir.name, videos=videos))

            if chapters:
                formations.append(Formation(name=formation_dir.name, chapters=chapters))

        return CatalogResponse(formations=formations)

    def _save_to_db(self, catalog: CatalogResponse) -> None:
        from src.database import SessionLocal
        from src.crud.formation import sync_catalog

        videos_path = self._get_videos_path()
        with SessionLocal() as db:
            sync_catalog(db, catalog, videos_path)
        logger.info("Catalog saved to database")

    def _load_from_db(self) -> CatalogResponse | None:
        from src.database import SessionLocal
        from src.crud.formation import get_formations

        videos_path = self._get_videos_path()
        with SessionLocal() as db:
            formations_db = get_formations(db)
            if not formations_db:
                return None

            formations: list[Formation] = []
            for f_db in formations_db:
                chapters: list[Chapter] = []
                for c_db in f_db.chapters:
                    videos: list[Video] = []
                    for v_db in c_db.videos:
                        abs_path = videos_path / v_db.path
                        self._video_path_map[v_db.id] = abs_path
                        videos.append(
                            Video(
                                id=v_db.id,
                                title=v_db.title,
                                path=str(abs_path),
                                duration=v_db.duration,
                            )
                        )
                    if videos:
                        chapters.append(Chapter(name=c_db.name, videos=videos))
                if chapters:
                    formations.append(Formation(name=f_db.name, chapters=chapters))

        if not formations:
            return None

        catalog = CatalogResponse(formations=formations)
        logger.info(f"Catalog loaded from database: {len(formations)} formations")
        return catalog

    def refresh(self) -> None:
        """Refresh the catalog by scanning the disk and persisting to the database."""
        videos_path = self._get_videos_path()
        logger.info(f"Scanning videos directory: {videos_path}")
        self._catalog = self._scan_directory(videos_path)
        logger.info(f"Catalog refreshed: {len(self._catalog.formations)} formations")
        self._save_to_db(self._catalog)

    def get_catalog(self) -> CatalogResponse:
        """Get the catalog, loading from DB if not in memory, otherwise refreshing from disk."""  # noqa: E501
        if self._catalog is None:
            db_catalog = self._load_from_db()
            if db_catalog is not None:
                self._catalog = db_catalog
            else:
                self.refresh()
        return self._catalog

    def get_video_path(self, video_id: str) -> Path | None:
        """Get the file path for a video ID."""
        if self._catalog is None:
            self.refresh()
        return self._video_path_map.get(video_id)

    def video_exists(self, video_id: str) -> bool:
        """Check if a video exists in the catalog."""
        if self._catalog is None:
            self.refresh()
        return video_id in self._video_path_map

    def get_formation(self, formation_name: str) -> Formation | None:
        """Get a formation by name."""
        catalog = self.get_catalog()
        for formation in catalog.formations:
            if formation.name == formation_name:
                return formation
        return None


# Singleton instance
catalog_service = CatalogService()
