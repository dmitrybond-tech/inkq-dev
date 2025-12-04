"""Pydantic schemas for artist profile and onboarding."""
from __future__ import annotations

from typing import List, Literal, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class ArtistBase(BaseModel):
    """Base fields for artist profile metadata."""

    about: Optional[str] = None
    styles: List[str] = Field(default_factory=list)
    city: Optional[str] = None
    studio_id: Optional[int] = None
    session_price: Optional[int] = None
    instagram: Optional[str] = None
    telegram: Optional[str] = None


class ArtistOnboardingStepStatus(BaseModel):
    """Computed onboarding step completion flags for artist."""

    about_complete: bool
    media_complete: bool
    portfolio_complete: bool
    wannado_complete: bool
    # 1–4, where 4 is the last step (wannado or "all done")
    first_incomplete_step: int


class ArtistMeResponse(ArtistBase):
    """Detailed response for the current authenticated artist."""

    username: str
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    onboarding_completed: bool
    steps: ArtistOnboardingStepStatus

    model_config = {"from_attributes": True}


class ArtistUpdateRequest(ArtistBase):
    """Update payload for current artist (all fields optional)."""

    onboarding_completed: Optional[bool] = None


class PortfolioItem(BaseModel):
    """Public portfolio item representation."""

    id: int
    url: str
    width: int
    height: int
    kind: Literal["portfolio", "wannado"]
    title: Optional[str] = None
    description: Optional[str] = None
    approx_price: Optional[str] = None
    placement: Optional[str] = None

    model_config = {"from_attributes": True}


class ArtistStudioShort(BaseModel):
    """Short studio info for artist public page."""

    id: int
    slug: str
    display_name: str
    avatar_url: Optional[str] = None


class PublicArtistResponse(BaseModel):
    """Public-facing artist profile response."""

    username: str
    about: Optional[str] = None
    styles: List[str] = Field(default_factory=list)
    city: Optional[str] = None
    session_price: Optional[int] = None
    instagram: Optional[str] = None
    telegram: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    portfolio: List[PortfolioItem] = Field(default_factory=list)
    wannado: List[PortfolioItem] = Field(default_factory=list)
    studios: List[ArtistStudioShort] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PublicArtistCard(BaseModel):
    """Public-facing artist card for catalog listing."""

    id: int
    username: str
    slug: str
    display_name: Optional[str] = None
    city: Optional[str] = None
    styles: List[str] = Field(default_factory=list)
    price_from: Optional[int] = None
    price_currency: str = "EUR"
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None


class PublicArtistListResponse(BaseModel):
    """Paginated list response for public artists catalog."""

    items: List[PublicArtistCard]
    total: int
    limit: int
    offset: int


class PublicArtistStyle(BaseModel):
    """Available tattoo styles for filters."""

    id: str
    label_en: str
    label_ru: str


class PublicArtistFiltersResponse(BaseModel):
    """Available filters for public artists catalog."""

    cities: List[str]
    styles: List[PublicArtistStyle]

