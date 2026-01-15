import hashlib
import logging
from pathlib import Path
from typing import Any

import ffmpeg

from src.config import settings
from src.database.schemas.catalog import CatalogResponse, Formation, Chapter, Video

logger = logging.getLogger(__name__)


class CatalogService:
    """Service for scanning and caching the video catalog from disk."""

    def __init__(self):
        self._catalog: CatalogResponse | None = None
        self._video_path_map: dict[str, Path] = {}

    def _get_video_duration(self, video_path: Path) -> float:
        """Extract video duration using ffmpeg."""
        try:
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe["format"]["duration"])
            return duration
        except Exception as e:
            logger.warning(f"Failed to get duration for {video_path}: {e}")
            return 0.0

    def _generate_video_id(self, video_path: Path) -> str:
        """Generate SHA1 hash of absolute path as video ID."""
        absolute_path = str(video_path.resolve())
        return hashlib.sha1(absolute_path.encode()).hexdigest()

    def _extract_title_from_filename(self, filename: str) -> str:
        """Extract title from filename, removing numeric prefix if present."""
        # Remove .mp4 extension
        name = filename.replace(".mp4", "")
        # Remove numeric prefix like "01 - " if present
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

        # Iterate over formation directories
        for formation_dir in sorted(videos_path.iterdir()):
            if not formation_dir.is_dir():
                continue

            formation_name = formation_dir.name
            chapters: list[Chapter] = []

            # Iterate over chapter directories
            for chapter_dir in sorted(formation_dir.iterdir()):
                if not chapter_dir.is_dir():
                    continue

                chapter_name = chapter_dir.name
                videos: list[Video] = []

                # Iterate over video files
                for video_file in sorted(chapter_dir.glob("*.mp4")):
                    if not video_file.is_file():
                        continue

                    video_id = self._generate_video_id(video_file)
                    title = self._extract_title_from_filename(video_file.name)
                    duration = self._get_video_duration(video_file)

                    # Store path mapping
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
                    chapters.append(Chapter(name=chapter_name, videos=videos))

            if chapters:
                formations.append(Formation(name=formation_name, chapters=chapters))

        return CatalogResponse(formations=formations)

    def refresh(self) -> None:
        """Refresh the catalog by scanning the disk."""
        videos_path = Path(settings.VIDEOS_PATH)
        if not videos_path.is_absolute():
            # Make relative to project root
            project_root = Path(__file__).parent.parent.parent
            videos_path = project_root / videos_path

        logger.info(f"Scanning videos directory: {videos_path}")
        self._catalog = self._scan_directory(videos_path)
        logger.info(f"Catalog refreshed: {len(self._catalog.formations)} formations")

    def get_catalog(self) -> CatalogResponse:
        """Get the catalog, refreshing if necessary."""
        if self._catalog is None:
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
