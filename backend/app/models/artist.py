"""Artist model."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class Artist(Base):
    """Artist role model - 1-1 with User."""

    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Optional display name (minimal for now)
    display_name = Column(String, nullable=True)
    # Slug for public URLs (unique per artist)
    slug = Column(String(255), nullable=True, unique=True, index=True)

    # Onboarding/profile metadata
    about = Column(Text, nullable=True)
    # Store style IDs as JSON array of strings
    styles = Column(JSONB, nullable=False, default=list)
    city = Column(String, nullable=True)
    # Optional link to a studio (simple integer FK/id for now)
    studio_id = Column(Integer, nullable=True)
    # Session price in base currency (e.g. smallest unit, integer)
    session_price = Column(Integer, nullable=True)
    instagram = Column(String, nullable=True)
    telegram = Column(String, nullable=True)

    # Relationship back to User
    user = relationship("User", back_populates="artist")

    # Relationship to studio residency invites
    studio_residencies = relationship(
        "ArtistStudioResident",
        back_populates="artist",
        cascade="all, delete-orphan",
    )

    # Optional booking requests targeting this artist
    booking_requests = relationship(
        "BookingRequest",
        back_populates="artist",
        cascade="all, delete-orphan",
    )
