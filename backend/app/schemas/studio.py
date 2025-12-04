"""Pydantic schemas for studio profile, residents and booking."""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class StudioBase(BaseModel):
    """Base fields for studio profile metadata."""

    name: Optional[str] = None
    about: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    instagram: Optional[str] = None
    telegram: Optional[str] = None
    vk: Optional[str] = None
    session_price_label: Optional[str] = None


class StudioMeResponse(StudioBase):
    """Detailed response for the current authenticated studio."""

    username: str
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    onboarding_completed: bool

    model_config = {"from_attributes": True}


class StudioUpdateRequest(StudioBase):
    """Update payload for current studio (all fields optional)."""

    onboarding_completed: Optional[bool] = None


class StudioResidentArtist(BaseModel):
    """Minimal public artist data embedded in studio resident responses."""

    id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    styles: List[str] = Field(default_factory=list)
    status: Literal["invited", "accepted", "rejected"]
    created_at: datetime


class StudioResidentsResponse(BaseModel):
    """List of residents for the current studio."""

    items: List[StudioResidentArtist]


class StudioResidentInviteRequest(BaseModel):
    """Request payload for inviting an artist to a studio."""

    identifier: str = Field(
        ...,
        description="Artist username or email used to look up the artist.",
    )


class ArtistInvitationStudio(BaseModel):
    """Minimal studio data embedded in artist invitations."""

    id: int
    name: Optional[str] = None
    city: Optional[str] = None


class ArtistInvitationItem(BaseModel):
    """Invitation item for an artist."""

    id: int
    studio: ArtistInvitationStudio
    status: Literal["invited", "accepted", "rejected"]
    created_at: datetime


class ArtistInvitationsResponse(BaseModel):
    """List of studio invitations for the current artist."""

    items: List[ArtistInvitationItem]


class PublicStudioTeamMember(BaseModel):
    """Public team member on studio public page."""

    artist_id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    styles: List[str] = Field(default_factory=list)


class PublicStudioPortfolioItem(BaseModel):
    """Public portfolio item for studio gallery."""

    id: int
    image_url: str
    width: int
    height: int


class PublicStudioInfo(StudioBase):
    """Public studio basic info."""

    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    instagram: Optional[str] = None
    telegram: Optional[str] = None
    vk: Optional[str] = None
    session_price_label: Optional[str] = None


class PublicStudioResponse(BaseModel):
    """Public-facing studio page response."""

    studio: PublicStudioInfo
    username: str
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    gallery: List[PublicStudioPortfolioItem] = Field(default_factory=list)
    team: List[PublicStudioTeamMember] = Field(default_factory=list)
    aggregated_styles: List[str] = Field(default_factory=list)


class PublicStudioCard(BaseModel):
    """Public-facing studio card for catalog listing."""

    id: int
    username: str
    slug: str
    name: Optional[str] = None
    city: Optional[str] = None
    session_price_label: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None


class PublicStudioListResponse(BaseModel):
    """Paginated list response for public studios catalog."""

    items: List[PublicStudioCard]
    total: int
    limit: int
    offset: int


class BookingRequestCreate(BaseModel):
    """Public booking request create payload."""

    type: Literal["general", "artist_specific"]
    client_name: str
    client_contact: str
    comment: Optional[str] = None
    artist_id: Optional[int] = None


class BookingRequestItem(BaseModel):
    """Booking request item returned to studios."""

    id: int
    studio_id: int
    artist_id: Optional[int] = None
    type: Literal["general", "artist_specific"]
    client_name: str
    client_contact: str
    comment: Optional[str] = None
    status: Literal["new", "in_progress", "closed"]
    created_at: datetime


class BookingRequestListResponse(BaseModel):
    """List of booking requests for a studio."""

    items: List[BookingRequestItem]


class BookingRequestUpdate(BaseModel):
    """Update payload for a booking request (status only)."""

    status: Literal["new", "in_progress", "closed"]


