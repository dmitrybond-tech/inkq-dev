"""Media-related schemas."""
from pydantic import BaseModel
from typing import List, Optional


class MediaUploadResponse(BaseModel):
    """Response for successful media upload."""
    url: str
    width: int
    height: int


class PortfolioImageResponse(BaseModel):
    """Response for portfolio image."""
    id: int
    user_id: int
    kind: str
    url: str
    width: int
    height: int
    mime_type: str
    created_at: str

    # Optional metadata fields (may be null / omitted)
    title: Optional[str] = None
    description: Optional[str] = None
    approx_price: Optional[str] = None
    placement: Optional[str] = None
    
    class Config:
        from_attributes = True


class PortfolioListResponse(BaseModel):
    """Response for portfolio list."""
    items: List[PortfolioImageResponse]


class PortfolioUploadResponse(BaseModel):
    """Response for portfolio upload (multiple images)."""
    items: List[PortfolioImageResponse]


class PortfolioImageUpdateRequest(BaseModel):
    """Partial update payload for portfolio image metadata."""

    title: Optional[str] = None
    description: Optional[str] = None
    approx_price: Optional[str] = None
    placement: Optional[str] = None

