#!/usr/bin/env python3
"""
Script to transcribe videos using the TranscriptionService and CatalogService.

This script allows you to:
- Select videos from the catalog by video ID
- Choose transcription options (model size, language, timecodes)
- Save transcriptions to files
"""

import click
import sys
from pathlib import Path

from src.services.transcription import TranscriptionService
from src.services.catalog import catalog_service


def list_videos():
    """List all available videos from the catalog."""
    catalog = catalog_service.get_catalog()

    if not catalog.formations:
        click.echo("❌ Aucune formation trouvée dans le catalogue.")
        return

    click.echo("\n📚 Vidéos disponibles dans le catalogue:\n")

    for formation in catalog.formations:
        click.echo(f"📖 Formation: {formation.name}")
        for chapter in formation.chapters:
            click.echo(f"  📁 Chapitre: {chapter.name}")
            for video in chapter.videos:
                duration_min = int(video.duration // 60)
                duration_sec = int(video.duration % 60)
                click.echo(
                    f"    🎬 [{video.id}] {video.title} ({duration_min}m {duration_sec}s)"
                )
        click.echo()


def get_all_videos(formation_name: str | None = None) -> list[tuple[str, Path, dict]]:
    """
    Get all videos from the catalog, optionally filtered by formation.

    Returns:
        List of tuples: (video_id, video_path, video_info_dict)
    """
    catalog = catalog_service.get_catalog()
    videos = []

    for formation in catalog.formations:
        # Filtrer par formation si spécifiée
        if formation_name and formation.name != formation_name:
            continue

        for chapter in formation.chapters:
            for video in chapter.videos:
                video_path = catalog_service.get_video_path(video.id)
                if video_path and video_path.exists():
                    videos.append(
                        (
                            video.id,
                            video_path,
                            {
                                "title": video.title,
                                "formation": formation.name,
                                "chapter": chapter.name,
                            },
                        )
                    )

    return videos


@click.command()
@click.option(
    "--video-id", "-v", help="ID de la vidéo à transcrire (obtenu via --list)"
)
@click.option(
    "--list",
    "-l",
    "list_videos_flag",
    is_flag=True,
    default=False,
    help="Liste toutes les vidéos disponibles dans le catalogue",
)
@click.option(
    "--model",
    "-m",
    type=click.Choice(
        ["tiny", "base", "small", "medium", "large"], case_sensitive=False
    ),
    default="base",
    help="Taille du modèle Whisper à utiliser (défaut: base)",
)
@click.option(
    "--language",
    "-lang",
    default="fr",
    help="Code de langue ISO 639-1 (ex: fr, en, es). Laissez vide pour la détection automatique (défaut: fr)",
)
@click.option(
    "--timecodes",
    "-t",
    is_flag=True,
    default=False,
    help="Inclure les timecodes dans la transcription (au niveau des segments)",
)
@click.option(
    "--word-timecodes",
    "-wt",
    is_flag=True,
    default=False,
    help="Inclure les timecodes au niveau des mots (plus détaillé que --timecodes)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True),
    help="Fichier de sortie pour la transcription (défaut: {video_name}.txt dans le même répertoire)",
)
@click.option(
    "--refresh-catalog",
    "-r",
    is_flag=True,
    default=False,
    help="Rafraîchir le catalogue avant de lister ou transcrire",
)
@click.option(
    "--all",
    "-a",
    "process_all",
    is_flag=True,
    default=False,
    help="Transcrire toutes les vidéos du catalogue",
)
@click.option(
    "--formation", "-f", help="Transcrire toutes les vidéos d'une formation spécifique"
)
@click.option(
    "--skip-existing",
    "-s",
    is_flag=True,
    default=False,
    help="Ignorer les vidéos déjà transcrites",
)
def main(
    video_id: str | None,
    list_videos_flag: bool,
    model: str,
    language: str,
    timecodes: bool,
    word_timecodes: bool,
    output: str | None,
    refresh_catalog: bool,
    process_all: bool,
    formation: str | None,
    skip_existing: bool,
):
    """
    Transcrit une vidéo en utilisant le TranscriptionService et le CatalogService.

    Vous devez soit spécifier --video-id, soit utiliser --list pour voir les vidéos disponibles.

    Exemples:

    \b
        # Lister les vidéos disponibles
        transcribev2.py --list

        # Transcrire une vidéo par son ID
        transcribev2.py --video-id abc123def456

        # Transcrire avec un modèle plus grand et des timecodes
        transcribev2.py --video-id abc123def456 --model medium --timecodes

        # Transcrire avec des timecodes au niveau des mots
        transcribev2.py --video-id abc123def456 --word-timecodes
    """
    click.echo("🎬 Script de transcription de vidéos")
    click.echo("=" * 60)

    # Rafraîchir le catalogue si demandé
    if refresh_catalog:
        click.echo("\n🔄 Rafraîchissement du catalogue...")
        catalog_service.refresh()
        click.echo("✅ Catalogue rafraîchi.\n")

    # Lister les vidéos si demandé
    if list_videos_flag:
        list_videos()
        return

    # Créer le service de transcription avec les paramètres choisis
    transcription_service = TranscriptionService(
        model_size=model,  # type: ignore
        language=language if language else None,
    )

    # Déterminer le format de sortie
    format_with_timecodes = timecodes or word_timecodes
    use_word_timestamps = word_timecodes

    # Traiter toutes les vidéos si demandé
    if process_all or formation:
        if video_id:
            click.echo(
                "\n❌ Erreur: --video-id ne peut pas être utilisé avec --all ou --formation.\n",
                err=True,
            )
            sys.exit(1)

        videos = get_all_videos(formation)

        if not videos:
            click.echo(
                f"\n❌ Aucune vidéo trouvée{f' pour la formation "{formation}"' if formation else ''}.\n",
                err=True,
            )
            sys.exit(1)

        click.echo(
            f"\n📹 {len(videos)} vidéo(s) à transcrire{f' (formation: {formation})' if formation else ''}\n"
        )
        click.echo(f"🧠 Modèle: {model}")
        click.echo(f"🌐 Langue: {language if language else 'auto'}")
        if format_with_timecodes:
            click.echo(
                f"⏱️  Timecodes: {'au niveau des mots' if word_timecodes else 'au niveau des segments'}"
            )
        click.echo()

        if not click.confirm("Voulez-vous continuer ?", default=True):
            click.echo("❌ Opération annulée.")
            sys.exit(0)

        success_count = 0
        skip_count = 0
        error_count = 0

        for idx, (vid_id, vid_path, vid_info) in enumerate(videos, 1):
            click.echo(f"\n{'=' * 60}")
            click.echo(f"[{idx}/{len(videos)}] {vid_info['title']}")
            click.echo(
                f"Formation: {vid_info['formation']} | Chapitre: {vid_info['chapter']}"
            )
            click.echo(f"Fichier: {vid_path}")
            click.echo(f"{'=' * 60}\n")

            # Vérifier si la transcription existe déjà
            if skip_existing and transcription_service.transcription_exists(vid_path):
                click.echo("⏭️  Transcription déjà existante, ignorée.")
                skip_count += 1
                continue

            try:
                click.echo(
                    "✍️  Début de la transcription (cela peut prendre du temps)..."
                )
                transcription_text = transcription_service.transcribe_to_text(
                    vid_path,
                    word_timestamps=use_word_timestamps,
                    format_with_timecodes=format_with_timecodes,
                )

                transcription_service.save_transcription(transcription_text, vid_path)
                click.echo("✅ Transcription terminée et sauvegardée!")
                success_count += 1

            except Exception as e:
                click.echo(f"❌ Erreur lors de la transcription: {e}", err=True)
                error_count += 1
                continue

        # Résumé final
        click.echo(f"\n{'=' * 60}")
        click.echo("📊 RÉSUMÉ")
        click.echo(f"{'=' * 60}")
        click.echo(f"✅ Succès: {success_count}")
        click.echo(f"⏭️  Ignorées: {skip_count}")
        click.echo(f"❌ Erreurs: {error_count}")
        click.echo(f"{'=' * 60}\n")

        return

    # Vérifier qu'un video_id est fourni
    if not video_id:
        click.echo(
            "\n❌ Erreur: Vous devez spécifier --video-id, --all, --formation ou utiliser --list pour voir les vidéos disponibles.\n",
            err=True,
        )
        click.echo("💡 Utilisez --list pour voir toutes les vidéos disponibles.")
        sys.exit(1)

    # Obtenir le chemin de la vidéo depuis le catalogue
    video_path = catalog_service.get_video_path(video_id)

    if not video_path:
        click.echo(
            f"\n❌ Erreur: Vidéo avec l'ID '{video_id}' introuvable dans le catalogue.",
            err=True,
        )
        click.echo("\n💡 Utilisez --list pour voir toutes les vidéos disponibles.")
        sys.exit(1)

    if not video_path.exists():
        click.echo(
            f"\n❌ Erreur: Le fichier vidéo n'existe pas: {video_path}", err=True
        )
        sys.exit(1)

    # Obtenir les informations de la vidéo depuis le catalogue
    catalog = catalog_service.get_catalog()
    video_info = None
    formation_info = None
    chapter_info = None

    for formation in catalog.formations:
        for chapter in formation.chapters:
            for video in chapter.videos:
                if video.id == video_id:
                    video_info = video
                    formation_info = formation
                    chapter_info = chapter
                    break
            if video_info:
                break
        if video_info:
            break

    if video_info:
        click.echo(f"\n📹 Vidéo: {video_info.title}")
        click.echo(f"📁 Formation: {formation_info.name if formation_info else 'N/A'}")
        click.echo(f"📂 Chapitre: {chapter_info.name if chapter_info else 'N/A'}")
        click.echo(f"📄 Fichier: {video_path}\n")

    click.echo(f"🧠 Modèle: {model}")
    click.echo(f"🌐 Langue: {language if language else 'auto'}")
    if format_with_timecodes:
        click.echo(
            f"⏱️  Timecodes: {'au niveau des mots' if word_timecodes else 'au niveau des segments'}"
        )
    click.echo()

    # Transcrire la vidéo
    try:
        click.echo("✍️  Début de la transcription (cela peut prendre du temps)...")
        transcription_text = transcription_service.transcribe_to_text(
            video_path,
            word_timestamps=use_word_timestamps,
            format_with_timecodes=format_with_timecodes,
        )

        click.echo("✅ Transcription terminée!\n")

        # Déterminer le fichier de sortie
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(transcription_text)
            click.echo(f"📄 Transcription sauvegardée dans: {output_path}")
        else:
            # Sauvegarder à l'emplacement par défaut (à côté de la vidéo)
            output_path = transcription_service.get_transcription_file_path(video_path)
            transcription_service.save_transcription(transcription_text, video_path)
            click.echo(f"📄 Transcription sauvegardée dans: {output_path}")

        # Afficher un aperçu
        click.echo("\n--- APERÇU DE LA TRANSCRIPTION ---")
        preview_lines = transcription_text.split("\n")[:5]
        for line in preview_lines:
            click.echo(line)
        if len(transcription_text.split("\n")) > 5:
            click.echo("...")
        click.echo("-----------------------------------\n")

    except FileNotFoundError as e:
        click.echo(f"❌ Erreur: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Erreur lors de la transcription: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
