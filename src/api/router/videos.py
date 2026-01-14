import fastapi
from fastapi.responses import StreamingResponse
from starlette.requests import Request

from src.services.catalog import catalog_service
from src.exceptions.video import VideoNotFoundError


router = fastapi.APIRouter(prefix="/videos", tags=["videos"])


@router.get("/{video_id}/stream")
async def stream_video(video_id: str, request: Request):
    """
    Stream a video file with Range request support for seeking.

    Args:
        video_id: The SHA1 hash of the video file path
        request: FastAPI request object

    Returns:
        StreamingResponse: The video file stream with appropriate headers
    """
    # Get video path from catalog
    video_path = catalog_service.get_video_path(video_id)
    if not video_path or not video_path.exists():
        raise VideoNotFoundError(video_id)

    file_size = video_path.stat().st_size

    # Handle Range requests
    range_header = request.headers.get("Range")
    if range_header:
        # Parse range header (e.g., "bytes=0-1023")
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1

        # Validate range
        if start < 0 or end >= file_size or start > end:
            raise fastapi.HTTPException(
                status_code=416, detail="Range Not Satisfiable"
            )

        # Read partial file
        def iterfile():
            with open(video_path, "rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(
            iterfile(), status_code=206, headers=headers
        )
    else:
        # Full file stream
        def iterfile():
            with open(video_path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk

        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(iterfile(), status_code=200, headers=headers)
