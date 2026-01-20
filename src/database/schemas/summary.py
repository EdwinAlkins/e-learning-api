from pydantic import BaseModel


class SummaryUpdateRequest(BaseModel):
    """Request model for updating a video summary."""

    summary: str


class SummaryResponse(BaseModel):
    """Response model for a video summary."""

    video_id: str
    summary: str
