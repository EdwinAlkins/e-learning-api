#!/usr/bin/env python3
"""
Script de migration des IDs de vidéos.

Ce script met à jour les IDs de vidéos dans la base de données pour passer
de l'ancien système (basé sur le chemin absolu) au nouveau système
(basé sur le chemin tronqué - 3 derniers niveaux).

Cela permet de conserver les commentaires et progrès existants lors du changement
de méthode de génération des IDs.
"""

import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

# Ajouter le répertoire racine au path pour les imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.database import SessionLocal
from src.database.models.note import Note
from src.database.models.progress import Progress

# Configuration du logging avec les paramètres de config
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _keep_last_levels(video_path: Path, depth: int) -> Path:
    """Garde les N derniers niveaux d'un chemin."""
    return Path(*video_path.parts[-depth:])


def _generate_old_video_id(video_path: Path) -> str:
    """Génère l'ancien ID basé sur le chemin absolu."""
    absolute_path = str(video_path.resolve())
    return hashlib.sha1(absolute_path.encode()).hexdigest()


def _generate_new_video_id(video_path: Path) -> str:
    """Génère le nouveau ID basé sur le chemin tronqué (3 derniers niveaux)."""
    truncated_path = str(_keep_last_levels(video_path, 3))
    return hashlib.sha1(truncated_path.encode()).hexdigest()


def _process_video_file(video_file: Path, videos_path: Path, id_mapping: Dict[str, str]) -> None:
    """Traite un fichier vidéo et ajoute son mapping au dictionnaire."""
    old_id = _generate_old_video_id(video_file)
    new_id = _generate_new_video_id(video_file)
    
    id_mapping[old_id] = new_id
    
    if old_id != new_id:
        logger.debug(
            f"Mapping: {old_id[:8]}... -> {new_id[:8]}... "
            f"({video_file.relative_to(videos_path)})"
        )


def scan_videos_and_build_mapping(videos_path: Path) -> Dict[str, str]:
    """
    Scanne tous les fichiers vidéo et crée un mapping entre ancien ID et nouveau ID.
    
    Returns:
        Dict[str, str]: Mapping {ancien_id: nouveau_id}
    """
    logger.info(f"Scanning videos directory: {videos_path}")
    
    if not videos_path.exists():
        logger.error(f"Videos directory does not exist: {videos_path}")
        return {}
    
    id_mapping: Dict[str, str] = {}
    video_count = 0
    
    # Parcourir toutes les formations
    for formation_dir in sorted(videos_path.iterdir()):
        if not formation_dir.is_dir():
            continue
        
        # Parcourir tous les chapitres
        for chapter_dir in sorted(formation_dir.iterdir()):
            if not chapter_dir.is_dir():
                continue
            
            # Parcourir tous les fichiers vidéo
            for video_file in sorted(chapter_dir.glob("*.mp4")):
                if video_file.is_file():
                    _process_video_file(video_file, videos_path, id_mapping)
                    video_count += 1
    
    logger.info(f"Found {video_count} videos, {len(id_mapping)} ID mappings created")
    return id_mapping


def migrate_notes(db: Session, id_mapping: Dict[str, str]) -> tuple[int, int]:
    """
    Met à jour les IDs de vidéos dans la table note.
    
    Returns:
        tuple[int, int]: (nombre de notes mises à jour, nombre de notes non migrées)
    """
    logger.info("Migrating notes...")
    
    # Récupérer toutes les notes
    stmt = select(Note)
    notes = db.execute(stmt).scalars().all()
    
    updated_count = 0
    not_migrated_count = 0
    
    for note in notes:
        old_id = note.video_id
        
        # Vérifier si cet ID doit être migré
        if old_id in id_mapping:
            new_id = id_mapping[old_id]
            if old_id != new_id:
                note.video_id = new_id
                updated_count += 1
                logger.debug(f"Note {note.id}: {old_id[:8]}... -> {new_id[:8]}...")
        else:
            # ID non trouvé dans le mapping (vidéo peut-être supprimée)
            not_migrated_count += 1
            logger.warning(
                f"Note {note.id}: video_id {old_id[:8]}... not found in mapping "
                f"(video may have been deleted)"
            )
    
    if updated_count > 0:
        db.commit()
        logger.info(f"Updated {updated_count} notes")
    
    if not_migrated_count > 0:
        logger.warning(f"{not_migrated_count} notes could not be migrated")
    
    return updated_count, not_migrated_count


def migrate_progress(db: Session, id_mapping: Dict[str, str]) -> tuple[int, int]:
    """
    Met à jour les IDs de vidéos dans la table progress.
    
    Returns:
        tuple[int, int]: (nombre de progrès mis à jour, nombre de progrès non migrés)
    """
    logger.info("Migrating progress...")
    
    # Récupérer tous les progrès
    stmt = select(Progress)
    progress_records = db.execute(stmt).scalars().all()
    
    updated_count = 0
    not_migrated_count = 0
    
    for progress in progress_records:
        old_id = progress.video_id
        
        # Vérifier si cet ID doit être migré
        if old_id in id_mapping:
            new_id = id_mapping[old_id]
            if old_id != new_id:
                progress.video_id = new_id
                updated_count += 1
                logger.debug(
                    f"Progress {progress.id} (user {progress.user_id}): "
                    f"{old_id[:8]}... -> {new_id[:8]}..."
                )
        else:
            # ID non trouvé dans le mapping (vidéo peut-être supprimée)
            not_migrated_count += 1
            logger.warning(
                f"Progress {progress.id} (user {progress.user_id}): "
                f"video_id {old_id[:8]}... not found in mapping "
                f"(video may have been deleted)"
            )
    
    if updated_count > 0:
        db.commit()
        logger.info(f"Updated {updated_count} progress records")
    
    if not_migrated_count > 0:
        logger.warning(f"{not_migrated_count} progress records could not be migrated")
    
    return updated_count, not_migrated_count


def main():
    """Fonction principale du script de migration."""
    logger.info("=" * 60)
    logger.info("Starting video ID migration")
    logger.info("=" * 60)
    
    # Obtenir le chemin des vidéos depuis la configuration
    videos_path = Path(settings.VIDEOS_PATH)
    if not videos_path.is_absolute():
        # Si le chemin est relatif, le rendre relatif à la racine du projet
        videos_path = project_root / videos_path
    
    logger.info(f"Videos path: {videos_path}")
    logger.info(f"Database path: {settings.DATABASE_PATH}")
    
    # Scanner les vidéos et créer le mapping
    id_mapping = scan_videos_and_build_mapping(videos_path)
    
    if not id_mapping:
        logger.error("No videos found or mapping is empty. Aborting migration.")
        return
    
    # Compter combien d'IDs changent réellement
    changed_ids = sum(1 for old, new in id_mapping.items() if old != new)
    logger.info(f"IDs that will change: {changed_ids} out of {len(id_mapping)}")
    
    if changed_ids == 0:
        logger.info("No IDs need to be migrated. All IDs are already using the new format.")
        return
    
    # Se connecter à la base de données
    db = SessionLocal()
    try:
        # Migrer les notes
        notes_updated, notes_not_migrated = migrate_notes(db, id_mapping)
        
        # Migrer les progrès
        progress_updated, progress_not_migrated = migrate_progress(db, id_mapping)
        
        # Résumé
        logger.info("=" * 60)
        logger.info("Migration summary:")
        logger.info(f"  Notes updated: {notes_updated}")
        logger.info(f"  Notes not migrated: {notes_not_migrated}")
        logger.info(f"  Progress updated: {progress_updated}")
        logger.info(f"  Progress not migrated: {progress_not_migrated}")
        logger.info("=" * 60)
        
        if notes_updated > 0 or progress_updated > 0:
            logger.info("✅ Migration completed successfully!")
        else:
            logger.info("ℹ️  No records needed to be updated.")
            
    except Exception as e:
        logger.error(f"Error during migration: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
