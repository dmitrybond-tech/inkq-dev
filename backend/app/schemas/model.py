"""Pydantic schemas for model profile and public model page."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ModelBase(BaseModel):
    """Base fields for model profile metadata."""

    display_name: Optional[str] = None
    about: Optional[str] = None
    city: Optional[str] = None
    instagram: Optional[str] = None
    telegram: Optional[str] = None


class ModelMeResponse(ModelBase):
    """Detailed response for the current authenticated model."""

    username: str
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    onboarding_completed: bool

    model_config = {"from_attributes": True}


class ModelUpdateRequest(ModelBase):
    """Update payload for current model (all fields optional)."""

    onboarding_completed: Optional[bool] = None


class ModelGalleryItem(BaseModel):
    """Gallery item for model private/public views."""

    id: int
    image_url: str
    caption: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelGalleryListResponse(BaseModel):
    """List of gallery items for current model."""

    items: List[ModelGalleryItem]


class PublicModelResponse(BaseModel):
    """Public-facing model profile response."""

    username: str
    display_name: Optional[str] = None
    city: Optional[str] = None
    about: Optional[str] = None
    instagram: Optional[str] = None
    telegram: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    gallery: List[ModelGalleryItem] = []

    model_config = {"from_attributes": True}


class PublicModelCard(BaseModel):
    """Public-facing model card for catalog listing."""

    id: int
    username: str
    slug: str
    display_name: Optional[str] = None
    city: Optional[str] = None
    styles: List[str] = Field(default_factory=list)
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None


class PublicModelListResponse(BaseModel):
    """Paginated list response for public models catalog."""

    items: List[PublicModelCard]
    total: int
    limit: int
    offset: int


