from pathlib import Path
import ffmpeg

def extract_thumbnail(video_path, output_path, time_sec=1):
    video_path = Path(video_path)
    output_path = Path(output_path)

    if not video_path.exists():
        raise FileNotFoundError(video_path)
    
    stream = ffmpeg.input(str(video_path), ss=time_sec)
    stream = ffmpeg.output(stream, str(output_path), vframes=1, qscale=2)
    ffmpeg.run(stream, overwrite_output=True)

# Exemple
extract_thumbnail(
    "/home/william/Vidéos/formation/Udemy - Bien débuter avec Spring et Spring Boot pour Java/01 - Introduction/04 - Premier fonctionnel.mp4",
    "thumbnail.jpg",
    time_sec=2
)
