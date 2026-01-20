import hashlib
import json
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
        self._cache_path: Path | None = None

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
        """Generate SHA1 hash of absolute path as video ID."""
        truncated_path = str(self._keep_last_levels(video_path, 3))
        return hashlib.sha1(truncated_path.encode()).hexdigest()

    def _extract_title_from_filename(self, filename: str) -> str:
        """Extract title from filename, removing numeric prefix if present."""
        # Remove .mp4 extension
        name = filename.replace(".mp4", "")
        # Remove numeric prefix like "01 - " if present
        parts = name.split(" - ", 1)
        if len(parts) == 2 and parts[0].strip().isdigit():
            return parts[1].strip()
        return name.strip()

    def _get_cache_path(self) -> Path:
        """Get the cache file path."""
        if self._cache_path is None:
            cache_path = Path(settings.CATALOG_CACHE_PATH)
            if not cache_path.is_absolute():
                # Make relative to project root
                project_root = Path(__file__).parent.parent.parent
                cache_path = project_root / cache_path
            self._cache_path = cache_path
        return self._cache_path

    def _load_cache(self) -> CatalogResponse | None:
        """Load catalog from JSON cache file."""
        cache_path = self._get_cache_path()
        if not cache_path.exists():
            logger.debug(f"Cache file does not exist: {cache_path}")
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            catalog = CatalogResponse(**cache_data)
            logger.info(
                f"Catalog loaded from cache: {len(catalog.formations)} formations"
            )
            return catalog
        except Exception as e:
            logger.warning(f"Failed to load cache from {cache_path}: {e}")
            return None

    def _save_cache(self, catalog: CatalogResponse) -> None:
        """Save catalog to JSON cache file."""
        cache_path = self._get_cache_path()
        try:
            # Ensure parent directory exists
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(catalog.model_dump(), f, indent=2, ensure_ascii=False)
            logger.info(f"Catalog saved to cache: {cache_path}")
        except Exception as e:
            logger.error(f"Failed to save cache to {cache_path}: {e}")

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
        """Refresh the catalog by scanning the disk and update cache."""
        videos_path = Path(settings.VIDEOS_PATH)
        if not videos_path.is_absolute():
            # Make relative to project root
            project_root = Path(__file__).parent.parent.parent
            videos_path = project_root / videos_path

        logger.info(f"Scanning videos directory: {videos_path}")
        self._catalog = self._scan_directory(videos_path)
        logger.info(f"Catalog refreshed: {len(self._catalog.formations)} formations")

        # Save to cache
        if self._catalog is not None:
            self._save_cache(self._catalog)

    def get_catalog(self) -> CatalogResponse:
        """Get the catalog, loading from cache if available, otherwise refreshing."""
        if self._catalog is None:
            # Try to load from cache first
            cached_catalog = self._load_cache()
            if cached_catalog is not None:
                self._catalog = cached_catalog
                # Rebuild video_path_map from cached catalog
                self._rebuild_path_map()
            else:
                # No cache available, refresh by scanning
                self.refresh()
        return self._catalog

    def _rebuild_path_map(self) -> None:
        """Rebuild video_path_map from the current catalog."""
        self._video_path_map.clear()
        if self._catalog is None:
            return

        videos_path = Path(settings.VIDEOS_PATH)
        if not videos_path.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            videos_path = project_root / videos_path

        for formation in self._catalog.formations:
            for chapter in formation.chapters:
                for video in chapter.videos:
                    video_path = Path(video.path)
                    # If path is absolute and exists, use it as is
                    if video_path.is_absolute() and video_path.exists():
                        self._video_path_map[video.id] = video_path
                    else:
                        # Try to reconstruct path from formation/chapter structure
                        reconstructed_path = (
                            videos_path
                            / formation.name
                            / chapter.name
                            / video_path.name
                        )
                        if reconstructed_path.exists():
                            self._video_path_map[video.id] = reconstructed_path
                        else:
                            # Fallback: use the path as stored (might be relative)
                            self._video_path_map[video.id] = video_path

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
