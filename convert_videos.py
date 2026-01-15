#!/usr/bin/env python3
"""
Script pour convertir toutes les vidéos de la structure des formations
en utilisant ffmpeg avec les codecs libx264 et aac.

Usage:
    python convert_videos.py
    python convert_videos.py --formation "Nom de la formation"
    python convert_videos.py --dry-run  # Affiche les vidéos sans convertir
    python convert_videos.py --list  # Liste les formations disponibles
"""

import logging
from pathlib import Path

import click
import ffmpeg

from src.services.catalog import catalog_service

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def convert_video(input_path: Path, output_path: Path) -> bool:
    """
    Convertit une vidéo avec ffmpeg-python.
    
    Args:
        input_path: Chemin du fichier d'entrée
        output_path: Chemin du fichier de sortie
        
    Returns:
        True si la conversion réussit, False sinon
    """
    try:
        # Utiliser ffmpeg-python pour la conversion
        stream = ffmpeg.input(str(input_path))
        stream = ffmpeg.output(
            stream,
            str(output_path),
            vcodec="libx264",
            acodec="aac",
        )
        # Overwrite output file if it exists
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        return True
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else "Erreur inconnue"
        logger.error(f"Erreur lors de la conversion: {error_msg[:200]}")
        return False
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return False


def get_video_paths_for_formation(
    catalog, formation_name: str | None = None
) -> list[Path]:
    """
    Collecte les chemins de vidéos pour une formation spécifique ou toutes.
    
    Args:
        catalog: Le catalogue des formations
        formation_name: Nom de la formation à filtrer (None pour toutes)
        
    Returns:
        Liste des chemins de vidéos
    """
    video_paths: list[Path] = []
    
    for formation in catalog.formations:
        # Filtrer par formation si spécifiée
        if formation_name and formation.name != formation_name:
            continue
            
        for chapter in formation.chapters:
            for video in chapter.videos:
                video_path = Path(video.path)
                if video_path.exists():
                    video_paths.append(video_path)
                else:
                    logger.warning(f"Vidéo introuvable: {video_path}")
    
    return video_paths


@click.command()
@click.option(
    "--formation",
    "-f",
    help="Nom de la formation à convertir (sinon toutes les formations)",
)
@click.option(
    "--list",
    "-l",
    "list_formations",
    is_flag=True,
    default=False,
    help="Liste les formations disponibles",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Affiche les vidéos qui seraient converties sans les convertir",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Confirme automatiquement sans demander",
)
def main(
    formation: str | None,
    list_formations: bool,
    dry_run: bool,
    yes: bool,
) -> None:
    """Convertit les vidéos avec ffmpeg (libx264 + aac)."""
    click.echo("🎬 Script de conversion des vidéos")
    click.echo("=" * 60)

    # Utiliser CatalogService pour obtenir toutes les vidéos
    click.echo("\n🔍 Recherche des vidéos via CatalogService...")
    catalog = catalog_service.get_catalog()
    
    # Lister les formations disponibles
    if list_formations:
        click.echo("\n📚 Formations disponibles:\n")
        if not catalog.formations:
            click.echo("  ❌ Aucune formation trouvée.")
        else:
            for idx, formation_item in enumerate(catalog.formations, 1):
                video_count = sum(
                    len(chapter.videos) for chapter in formation_item.chapters
                )
                click.echo(f"  {idx}. {formation_item.name} ({video_count} vidéo(s))")
        return
    
    # Si une formation est spécifiée, vérifier qu'elle existe
    if formation:
        formation_names = [f.name for f in catalog.formations]
        if formation not in formation_names:
            click.echo(f"\n❌ Formation '{formation}' introuvable.")
            click.echo("\n📚 Formations disponibles:")
            for formation_item in catalog.formations:
                click.echo(f"  - {formation_item.name}")
            raise click.Abort()
    
    # Collecter les chemins de vidéos selon la formation choisie
    video_paths = get_video_paths_for_formation(catalog, formation)
    
    if not video_paths:
        if formation:
            click.echo(f"❌ Aucune vidéo trouvée pour la formation '{formation}'.")
        else:
            click.echo("❌ Aucune vidéo trouvée.")
        raise click.Abort()
    
    # Afficher le contexte
    if formation:
        click.echo(f"📚 Formation sélectionnée: {formation}")
    else:
        click.echo("📚 Toutes les formations seront converties")
    
    click.echo(f"✅ {len(video_paths)} vidéo(s) trouvée(s)\n")

    # Afficher les vidéos qui seront converties
    if dry_run:
        click.echo("📋 Vidéos qui seraient converties:\n")
        current_formation = None
        for video_path in video_paths:
            # Afficher le nom de la formation si elle change
            # Structure: videos/<formation>/<chapter>/<video>.mp4
            parts = video_path.parts
            if len(parts) >= 3:
                video_formation = parts[-3]
                if video_formation != current_formation:
                    current_formation = video_formation
                    click.echo(f"\n  📁 {video_formation}/")
                click.echo(f"    - {video_path.name}")
            else:
                click.echo(f"  - {video_path}")
        click.echo(f"\n📊 Total: {len(video_paths)} vidéo(s)")
        return

    # Demander confirmation
    if not yes:
        click.echo("⚠️  ATTENTION: Les fichiers originaux seront remplacés!")
        if formation:
            click.echo(f"⚠️  Formation concernée: {formation}")
        if not click.confirm("Continuer?", default=False):
            click.echo("❌ Conversion annulée.")
            return

    # Convertir chaque vidéo
    click.echo("\n🔄 Conversion en cours...\n")
    success_count = 0
    error_count = 0

    with click.progressbar(
        video_paths,
        label="Conversion",
        item_show_func=lambda x: str(x.name) if x else "",
    ) as bar:
        for video_path in bar:
            # Créer un fichier temporaire pour la sortie
            temp_output = video_path.with_suffix(".tmp.mp4")

            # Convertir
            if convert_video(video_path, temp_output):
                # Remplacer l'original par le fichier converti
                try:
                    video_path.unlink()  # Supprimer l'original
                    temp_output.rename(video_path)  # Renommer le temporaire
                    success_count += 1
                except Exception as e:
                    logger.error(f"Erreur lors du remplacement de {video_path}: {e}")
                    if temp_output.exists():
                        temp_output.unlink()  # Nettoyer le fichier temporaire
                    error_count += 1
            else:
                # Nettoyer le fichier temporaire en cas d'erreur
                if temp_output.exists():
                    temp_output.unlink()
                error_count += 1

    # Résumé
    click.echo("\n" + "=" * 60)
    click.echo(f"✅ Conversions réussies: {success_count}")
    click.echo(f"❌ Erreurs: {error_count}")
    click.echo(f"📊 Total: {len(video_paths)}")


if __name__ == "__main__":
    main()
