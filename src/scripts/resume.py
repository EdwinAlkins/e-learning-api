#!/usr/bin/env python3
"""
Script to generate summaries of videos using the SummaryService and TranscriptionService.

This script allows you to:
- Select videos from the catalog by video ID
- Generate summaries from transcriptions
- Automatically check if transcription exists and provide command to create it if missing
"""

import click
import sys
from pathlib import Path

from src.services.summary import summary_service
from src.services.transcription import transcription_service
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


def get_transcription_command(video_id: str) -> str:
    """Generate the command to transcribe a video."""
    script_path = Path(__file__).parent / "transcribe.py"
    return f"python {script_path} --video-id {video_id}"


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
@click.option("--video-id", "-v", help="ID de la vidéo à résumer (obtenu via --list)")
@click.option(
    "--list",
    "-l",
    "list_videos_flag",
    is_flag=True,
    default=False,
    help="Liste toutes les vidéos disponibles dans le catalogue",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True),
    help="Fichier de sortie pour le résumé (défaut: {video_name}.md dans le même répertoire)",
)
@click.option(
    "--refresh-catalog",
    "-r",
    is_flag=True,
    default=False,
    help="Rafraîchir le catalogue avant de lister ou résumer",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Forcer la régénération du résumé même s'il existe déjà",
)
@click.option(
    "--all",
    "-a",
    "process_all",
    is_flag=True,
    default=False,
    help="Résumer toutes les vidéos du catalogue",
)
@click.option(
    "--formation", "-form", help="Résumer toutes les vidéos d'une formation spécifique"
)
@click.option(
    "--skip-existing",
    "-s",
    is_flag=True,
    default=False,
    help="Ignorer les vidéos déjà résumées (sauf si --force est utilisé)",
)
def main(
    video_id: str | None,
    list_videos_flag: bool,
    output: str | None,
    refresh_catalog: bool,
    force: bool,
    process_all: bool,
    formation: str | None,
    skip_existing: bool,
):
    """
    Génère un résumé d'une vidéo en utilisant le SummaryService et le TranscriptionService.

    Vous devez soit spécifier --video-id, soit utiliser --list pour voir les vidéos disponibles.

    Le script vérifie d'abord si la transcription existe. Si elle n'existe pas,
    il affiche la commande à exécuter pour la créer.

    Exemples:

    \b
        # Lister les vidéos disponibles
        resumev3.py --list

        # Générer un résumé pour une vidéo
        resumev3.py --video-id abc123def456

        # Forcer la régénération du résumé
        resumev3.py --video-id abc123def456 --force
    """
    click.echo("📝 Script de résumé de vidéos")
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
            f"\n📹 {len(videos)} vidéo(s) à résumer{f' (formation: {formation})' if formation else ''}\n"
        )

        if not click.confirm("Voulez-vous continuer ?", default=True):
            click.echo("❌ Opération annulée.")
            sys.exit(0)

        success_count = 0
        skip_count = 0
        error_count = 0
        missing_transcription_count = 0

        for idx, (vid_id, vid_path, vid_info) in enumerate(videos, 1):
            click.echo(f"\n{'=' * 60}")
            click.echo(f"[{idx}/{len(videos)}] {vid_info['title']}")
            click.echo(
                f"Formation: {vid_info['formation']} | Chapitre: {vid_info['chapter']}"
            )
            click.echo(f"Fichier: {vid_path}")
            click.echo(f"{'=' * 60}\n")

            # Vérifier si la transcription existe
            if not transcription_service.transcription_exists(vid_path):
                click.echo("❌ La transcription n'existe pas pour cette vidéo.")
                click.echo(
                    f"💡 Pour créer la transcription, exécutez:\n   {get_transcription_command(vid_id)}\n"
                )
                missing_transcription_count += 1
                continue

            # Vérifier si le résumé existe déjà
            if not force and summary_service.summary_exists(vid_path):
                if skip_existing:
                    click.echo("⏭️  Résumé déjà existant, ignoré.")
                    skip_count += 1
                    continue
                else:
                    click.echo("ℹ️  Un résumé existe déjà pour cette vidéo.")
                    click.echo(
                        "💡 Utilisez --force pour régénérer ou --skip-existing pour ignorer.\n"
                    )
                    skip_count += 1
                    continue

            # Lire la transcription
            try:
                click.echo("📖 Lecture de la transcription...")
                transcription_text = transcription_service.get_transcription(vid_path)
                click.echo(
                    f"✅ Transcription lue ({len(transcription_text)} caractères)\n"
                )
            except Exception as e:
                click.echo(
                    f"❌ Erreur lors de la lecture de la transcription: {e}", err=True
                )
                error_count += 1
                continue

            # Générer le résumé
            try:
                click.echo("📤 Génération du résumé...")
                summary = summary_service.execute_summary(transcription_text)

                if summary is None:
                    click.echo("❌ Erreur: Impossible de générer le résumé.", err=True)
                    error_count += 1
                    continue

                # Sauvegarder le résumé
                summary_service.save_summary(summary, vid_path)
                click.echo(
                    f"✅ Résumé généré et sauvegardé ({len(summary)} caractères)"
                )
                success_count += 1

            except Exception as e:
                click.echo(f"❌ Erreur lors de la génération du résumé: {e}", err=True)
                error_count += 1
                continue

        # Résumé final
        click.echo(f"\n{'=' * 60}")
        click.echo("📊 RÉSUMÉ")
        click.echo(f"{'=' * 60}")
        click.echo(f"✅ Succès: {success_count}")
        click.echo(f"⏭️  Ignorées: {skip_count}")
        click.echo(f"❌ Erreurs: {error_count}")
        click.echo(f"📝 Transcriptions manquantes: {missing_transcription_count}")
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

    # Vérifier si la transcription existe
    if not transcription_service.transcription_exists(video_path):
        click.echo("❌ La transcription n'existe pas pour cette vidéo.")
        click.echo("\n💡 Pour créer la transcription, exécutez la commande suivante:\n")
        click.echo(f"   {get_transcription_command(video_id)}\n")
        click.echo("Une fois la transcription créée, vous pourrez générer le résumé.")
        sys.exit(1)

    # Vérifier si le résumé existe déjà
    if not force and summary_service.summary_exists(video_path):
        click.echo("ℹ️  Un résumé existe déjà pour cette vidéo.")
        click.echo(f"   Fichier: {summary_service.get_summary_file_path(video_path)}")
        click.echo("\n💡 Utilisez --force pour régénérer le résumé.\n")

        # Afficher le résumé existant
        try:
            existing_summary = summary_service.get_summary(video_path)
            click.echo("--- RÉSUMÉ EXISTANT ---")
            click.echo(existing_summary)
            click.echo("----------------------\n")
        except Exception as e:
            click.echo(f"⚠️  Erreur lors de la lecture du résumé existant: {e}\n")

        return

    # Lire la transcription
    try:
        click.echo("📖 Lecture de la transcription...")
        transcription_text = transcription_service.get_transcription(video_path)
        click.echo(f"✅ Transcription lue ({len(transcription_text)} caractères)\n")
    except FileNotFoundError:
        click.echo(
            f"❌ Erreur: La transcription n'existe pas: {transcription_service.get_transcription_file_path(video_path)}",
            err=True,
        )
        click.echo("\n💡 Pour créer la transcription, exécutez la commande suivante:\n")
        click.echo(f"   {get_transcription_command(video_id)}\n")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Erreur lors de la lecture de la transcription: {e}", err=True)
        sys.exit(1)

    # Générer le résumé
    try:
        click.echo("📤 Envoi de la transcription à Gemini pour génération du résumé...")
        click.echo(f"   📏 Taille du texte : {len(transcription_text)} caractères")
        click.echo("   ⏳ Traitement en cours... (cela peut prendre du temps)\n")

        summary = summary_service.execute_summary(transcription_text)

        if summary is None:
            click.echo("❌ Erreur: Impossible de générer le résumé.", err=True)
            click.echo("   Vérifiez que npx et @google/gemini-cli sont installés.")
            sys.exit(1)

        click.echo(f"✅ Résumé généré ({len(summary)} caractères)\n")

        # Déterminer le fichier de sortie
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(summary)
            click.echo(f"📄 Résumé sauvegardé dans: {output_path}")
        else:
            # Sauvegarder à l'emplacement par défaut (à côté de la vidéo)
            output_path = summary_service.get_summary_file_path(video_path)
            summary_service.save_summary(summary, video_path)
            click.echo(f"📄 Résumé sauvegardé dans: {output_path}")

        # Afficher le résumé
        click.echo("\n--- RÉSUMÉ GÉNÉRÉ ---")
        click.echo(summary)
        click.echo("---------------------\n")

    except Exception as e:
        click.echo(f"❌ Erreur lors de la génération du résumé: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
