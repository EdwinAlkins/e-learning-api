import logging
import tempfile
from pathlib import Path
from typing import Literal

import ffmpeg
import whisper


logger = logging.getLogger(__name__)

ModelSize = Literal["tiny", "base", "small", "medium", "large"]


class TranscriptionService:
    """Service for transcribing videos."""

    def __init__(self, model_size: ModelSize = "base", language: str = "fr"):
        """
        Initialize the transcription service.
        
        Args:
            model_size: Size of the Whisper model to use
            language: Language code (ISO 639-1) or None for auto-detection
        """
        self._model: whisper.Whisper | None = None
        self._model_size: ModelSize = model_size
        self._language: str | None = language if language else None

    def _get_model(self) -> whisper.Whisper:
        """Get the Whisper model, loading it if necessary."""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self._model_size}")
            self._model = whisper.load_model(self._model_size)
        return self._model
    
    def transcribe(
        self, 
        video_path: Path, 
        word_timestamps: bool = False
    ) -> dict:
        """
        Transcribe a video file.
        
        Args:
            video_path: Path to the video file
            word_timestamps: If True, include word-level timestamps
            
        Returns:
            Dictionary with transcription results:
            - 'text': Full transcription text
            - 'segments': List of segments with timestamps (if word_timestamps is True)
            - 'words': List of words with timestamps (if word_timestamps is True)
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        logger.info(f"Transcribing video: {video_path}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            try:
                self._convert_video_to_audio(video_path, temp_audio.name)
                model = self._get_model()
                
                # Configure transcription options
                transcribe_options = {
                    "language": self._language,
                }
                
                if word_timestamps:
                    transcribe_options["word_timestamps"] = True
                
                logger.info("Starting transcription...")
                result = model.transcribe(temp_audio.name, **transcribe_options)
                
                return result
            finally:
                # Clean up temporary audio file
                try:
                    Path(temp_audio.name).unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temporary audio file: {e}")
    
    def transcribe_to_text(
        self, 
        video_path: Path, 
        word_timestamps: bool = False,
        format_with_timecodes: bool = False
    ) -> str:
        """
        Transcribe a video file and return formatted text.
        
        Args:
            video_path: Path to the video file
            word_timestamps: If True, include word-level timestamps in output
            format_with_timecodes: If True, format output with timecodes
            
        Returns:
            Formatted transcription text
        """
        result = self.transcribe(video_path, word_timestamps=word_timestamps)
        
        if format_with_timecodes and word_timestamps and "segments" in result:
            # Format with segment timecodes
            lines = []
            for segment in result["segments"]:
                start_time = self._format_timestamp(segment["start"])
                end_time = self._format_timestamp(segment["end"])
                text = segment["text"].strip()
                lines.append(f"[{start_time} -> {end_time}] {text}")
            return "\n".join(lines)
        elif format_with_timecodes and word_timestamps and "words" in result:
            # Format with word-level timecodes
            words_with_times = []
            for word_info in result["words"]:
                word = word_info["word"].strip()
                start_time = self._format_timestamp(word_info["start"])
                words_with_times.append(f"[{start_time}] {word}")
            return " ".join(words_with_times)
        else:
            # Return plain text
            return result["text"]
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS.mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
        
    def _convert_video_to_audio(self, video_path: Path, audio_path: str) -> str:
        """Convert a video file to audio."""
        logger.debug(f"Converting video to audio: {video_path} -> {audio_path}")
        ffmpeg.input(str(video_path)).output(
            audio_path, 
            ar='16000', 
            ac='1', 
            loglevel='quiet'
        ).overwrite_output().run()
        return audio_path
    
    def get_transcription_file_path(self, video_path: Path) -> Path:
        """Get the transcription file path."""
        return Path(video_path.parent / f"{video_path.stem}.txt")
    
    def save_transcription(self, transcription: str, video_path: Path) -> None:
        """Save the transcription to a file."""
        output_path = self.get_transcription_file_path(video_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcription)
        logger.info(f"Transcription saved to: {output_path}")
    
    def get_transcription(self, video_path: Path) -> str:
        """Get the transcription from a file."""
        with open(self.get_transcription_file_path(video_path), "r", encoding="utf-8") as f:
            return f.read()
        
    def transcription_exists(self, video_path: Path) -> bool:
        """Check if the transcription exists."""
        return self.get_transcription_file_path(video_path).exists()

# Singleton
transcription_service = TranscriptionService()
logger.info("Transcription service initialized")
