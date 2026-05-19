import fastapi
import logging
from fastapi import Query
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from starlette.requests import Request
from starlette.exceptions import HTTPException

import sqlalchemy.orm as so

from src.services.catalog import catalog_service
from src.services.summary import summary_service
from src.exceptions.video import VideoNotFoundError
from src.database.schemas.summary import SummaryUpdateRequest, SummaryResponse
from src.crud.user import get_user_by_uid
from src.exceptions.user import UserNotFoundError
from src.database import get_db

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(prefix="/videos", tags=["videos"])

# Content type for video files
VIDEO_CONTENT_TYPE = "video/mp4"


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: str, 
    request: Request, 
    user_uid: str = Query(..., description="The UID of the user"),
    db: so.Session = fastapi.Depends(get_db)
):
    """
    Stream a video file with Range request support for seeking.
    Matches the behavior of the Express.js implementation.

    Args:
        video_id: The SHA1 hash of the video file path
        request: FastAPI request object

    Returns:
        StreamingResponse: The video file stream with appropriate headers
    """
    # Get user from database
    user = get_user_by_uid(db, user_uid)
    
    if not user:
        raise UserNotFoundError(user_uid)
    # Get video path from catalog
    video_path = catalog_service.get_video_path(video_id)
    if not video_path or not video_path.exists():
        raise VideoNotFoundError(video_id)

    file_size = video_path.stat().st_size

    # Handle Range requests (matching Express.js behavior)
    range_header = request.headers.get("Range")
    if range_header:
        # Parse range header exactly like Express.js: "bytes=0-1023" -> ["0", "1023"]
        parts = range_header.replace("bytes=", "").split("-")
        start = int(parts[0], 10) if parts[0] else 0
        end = int(parts[1], 10) if (len(parts) > 1 and parts[1]) else file_size - 1

        # Calculate chunk size (matching Express.js: (end - start) + 1)
        chunksize = (end - start) + 1

        # Read partial file
        def iterfile():
            with open(video_path, "rb") as f:
                f.seek(start)
                remaining = chunksize
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
            "Content-Length": str(chunksize),
            "Content-Type": VIDEO_CONTENT_TYPE,
        }
        # 206 = Partial Content (matching Express.js)
        return StreamingResponse(iterfile(), status_code=206, headers=headers)
    else:
        # Full file stream (when no Range header)
        def iterfile():
            with open(video_path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk

        headers = {
            "Content-Length": str(file_size),
            "Content-Type": VIDEO_CONTENT_TYPE,
        }
        # 200 = OK (matching Express.js)
        return StreamingResponse(iterfile(), status_code=200, headers=headers)


# @router.get("/{video_id}/file")
# async def get_video_file(video_id: str):
#     """
#     Download a video file.

#     Args:
#         video_id: The SHA1 hash of the video file path

#     Returns:
#         FileResponse: The video file for download
#     """
#     video_path = catalog_service.get_video_path(video_id)
#     if not video_path or not video_path.exists():
#         raise VideoNotFoundError(video_id)

#     return FileResponse(
#         video_path,
#         filename=video_path.name,
#         media_type="video/mp4",
#     )


@router.get("/{video_id}/file")
async def get_video_file(video_id: str):
    """
    Download a video file.

    Args:
        video_id: The SHA1 hash of the video file path

    Returns:
        FileResponse: The video file for download
    """
    video_path = catalog_service.get_video_path(video_id)
    if not video_path or not video_path.exists():
        raise VideoNotFoundError(video_id)

    return FileResponse(
        video_path,
        filename=video_path.name,
        media_type=VIDEO_CONTENT_TYPE,
    )


@router.get("/{video_id}/summary")
async def get_video_summary(
    video_id: str, 
    user_uid: str = Query(..., description="The UID of the user"),
    db: so.Session = fastapi.Depends(get_db)
):
    """
    Get the summary of a video.

    Args:
        video_id: The SHA1 hash of the video file path

    Returns:
        dict: The summary content in markdown format

    Raises:
        VideoNotFoundError: If the video does not exist
        HTTPException: 404 if the summary file does not exist
    """
    user = get_user_by_uid(db, user_uid)
    if not user:
        raise UserNotFoundError(user_uid)
    # Get video path from catalog
    video_path = catalog_service.get_video_path(video_id)
    if not video_path or not video_path.exists():
        raise VideoNotFoundError(video_id)

    # Check if summary exists
    if not summary_service.summary_exists(video_path):
        raise HTTPException(status_code=404, detail="Summary not found for this video")

    # Get and return the summary
    summary = summary_service.get_summary(video_path)
    return {"summary": summary}


@router.put("/{video_id}/summary")
async def update_video_summary(
    video_id: str, 
    request: SummaryUpdateRequest,
    user_uid: str = Query(..., description="The UID of the user"),
    db: so.Session = fastapi.Depends(get_db)
):
    """
    Update the summary of a video.

    Args:
        video_id: The SHA1 hash of the video file path
        request: The summary update request containing the new summary text

    Returns:
        dict: The updated summary content in markdown format

    Raises:
        VideoNotFoundError: If the video does not exist
        HTTPException: 404 if the summary file does not exist (user must first create it)
    """
    user = get_user_by_uid(db, user_uid)
    if not user:
        raise UserNotFoundError(user_uid)
    # Get video path from catalog
    video_path = catalog_service.get_video_path(video_id)
    if not video_path or not video_path.exists():
        raise VideoNotFoundError(video_id)

    # Check if summary exists (optional - we could create it if it doesn't exist)
    # For now, we require it to exist first
    if not summary_service.summary_exists(video_path):
        raise HTTPException(
            status_code=404,
            detail="Summary not found for this video. Please create it first.",
        )

    # Save the updated summary
    summary_service.save_summary(request.summary, video_path)

    # Return the updated summary
    return SummaryResponse(video_id=video_id, summary=request.summary)
