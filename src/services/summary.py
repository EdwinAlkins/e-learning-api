import subprocess
import sys
from pathlib import Path
import logging


logger = logging.getLogger(__name__)
PROMPT_SUMMARY = """
Tu es un assistant expert en synthèse et en rédaction et professeur. 
Fais un résumé concis et structuré du script complet d'une vidéo.
Objectif: produire un résumé clair et structuré. Je dois pouvoir l'utiliser comme fiche de révision.
Je veux qu'il soit au format Markdown. Pas de phrase d'introduction IA, je veux juste le résumé directement dans le retour du chat.

Voici le script complet de la vidéo:
{script}
"""


class SummaryService:
    """Service for summarizing videos."""

    def __init__(self, prompt_summary: str = PROMPT_SUMMARY):
        self._prompt_summary = prompt_summary

    def prompt_summary(self, script: str) -> str:
        """Prompt for summarizing a script."""
        return self._prompt_summary.format(script=script)

    def execute_summary(self, script: str) -> str | None:
        """
        Execute the summary.

        Returns:
            The summary text, or None if an error occurred.
        """
        try:
            cmd = [
                "npx",
                "--yes",
                "@google/gemini-cli",
                "-p",
                self.prompt_summary(script),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=600,  # Timeout de 10 minutes pour les gros textes
                cwd=Path(script).parent,
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Error executing summary: {error_msg}")
                return None

            summary = result.stdout.strip()

            if not summary:
                logger.warning("No summary received from Gemini")
                return None

            return summary
        except subprocess.TimeoutExpired:
            logger.error("Timeout: summary generation took too long (>10 minutes)")
            return None
        except Exception as e:
            logger.error(f"Error executing summary: {e}")
            return None

    def save_summary(self, summary: str, video_path: Path) -> None:
        """Save the summary to a file."""
        with open(self.get_summary_file_path(video_path), "w", encoding="utf-8") as f:
            f.write(summary)

    def get_summary(self, video_path: Path) -> str:
        """Get the summary from a file."""
        with open(self.get_summary_file_path(video_path), "r", encoding="utf-8") as f:
            return f.read()

    def get_summary_file_path(self, video_path: Path) -> Path:
        """Get the summary file path."""
        return Path(video_path.parent / f"{video_path.stem}.md")

    def summary_exists(self, video_path: Path) -> bool:
        """Check if the summary exists."""
        return self.get_summary_file_path(video_path).exists()


# Singleton
summary_service = SummaryService()
logger.info("Summary service initialized")
