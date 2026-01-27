import subprocess
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from openai import OpenAI

from src.config import settings


logger = logging.getLogger(__name__)

PROMPT_SUMMARY = """
Tu es un assistant expert en synthèse et en rédaction et professeur. 
Fais un résumé concis et structuré du script complet d'une vidéo.
Objectif: produire un résumé clair et structuré. Je dois pouvoir l'utiliser comme fiche de révision.
Je veux qu'il soit au format Markdown. Pas de phrase d'introduction IA, je veux juste le résumé directement dans le retour du chat.

Voici le script complet de la vidéo:
{script}
"""

def get_prompt_summary(script: str, prompt_summary: str) -> str:
    """Prompt for summarizing a script."""
    return prompt_summary.format(script=script)

class SummaryStrategy(ABC):
    """Strategy for summarizing a script."""
    @abstractmethod
    def summarize(self, script: str, prompt_summary: str) -> str | None:
        """Summarize a script."""
        pass
    
class GeminiSummaryStrategy(SummaryStrategy):
    """Strategy for summarizing a script using Gemini."""
    
    def summarize(self, script: str, prompt_summary: str) -> str | None:
        """Summarize a script using Gemini."""
        logger.info("Summarizing script using Gemini strategy")
        try:
            cmd = [
                "npx",
                "--yes",
                "@google/gemini-cli",
                "-p",
                get_prompt_summary(script, prompt_summary),
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
            
            ## add string signature to the summary strategy used at the end of the summary
            summary += "\n\nSummary generated using Gemini."

            return summary
        except subprocess.TimeoutExpired:
            logger.error("Timeout: summary generation took too long (>10 minutes)")
            return None
        except Exception as e:
            logger.error(f"Error executing summary: {e}")
            return None
        
class OpenAISummaryStrategy(SummaryStrategy):
    """Strategy for summarizing a script using OpenAI."""
    def summarize(self, script: str, prompt_summary: str) -> str | None:
        """Summarize a script using OpenAI."""
        logger.info("Summarizing script using OpenAI strategy")
        try:
            client = OpenAI(base_url=settings.OPENAI_BASE_URL, api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": get_prompt_summary(script, prompt_summary)}],
            )
            summary = response.choices[0].message.content
            ## add string signature to the summary strategy used at the end of the summary
            summary += "\n\nSummary generated using OpenAI."
            return summary
        except Exception as e:
            logger.error(f"Error executing summary: {e}")
            return None

class SummaryService:
    """Service for summarizing videos."""

    def __init__(self, prompt_summary: str = PROMPT_SUMMARY):
        self._prompt_summary = prompt_summary
        if settings.SUMMARY_STRATEGY == "openapi":
            self._summary_strategy = OpenAISummaryStrategy()
        elif settings.SUMMARY_STRATEGY == "gemini":
            self._summary_strategy = GeminiSummaryStrategy()
        else:
            raise ValueError(f"Invalid summary strategy: {settings.SUMMARY_STRATEGY}")

    def execute_summary(self, script: str) -> str | None:
        """
        Execute the summary.

        Returns:
            The summary text, or None if an error occurred.
        """
        return self._summary_strategy.summarize(script, self._prompt_summary)
        # try:
        #     cmd = [
        #         "npx",
        #         "--yes",
        #         "@google/gemini-cli",
        #         "-p",
        #         get_prompt_summary(script, self._prompt_summary),
        #     ]
        #     result = subprocess.run(
        #         cmd,
        #         capture_output=True,
        #         text=True,
        #         encoding="utf-8",
        #         timeout=600,  # Timeout de 10 minutes pour les gros textes
        #         cwd=Path(script).parent,
        #     )

        #     if result.returncode != 0:
        #         error_msg = result.stderr or result.stdout
        #         logger.error(f"Error executing summary: {error_msg}")
        #         return None

        #     summary = result.stdout.strip()

        #     if not summary:
        #         logger.warning("No summary received from Gemini")
        #         return None

        #     return summary
        # except subprocess.TimeoutExpired:
        #     logger.error("Timeout: summary generation took too long (>10 minutes)")
        #     return None
        # except Exception as e:
        #     logger.error(f"Error executing summary: {e}")
        #     return None

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
