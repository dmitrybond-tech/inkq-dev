"""Studio model."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Studio(Base):
    """Studio role model - 1-1 with User."""

    __tablename__ = "studios"

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

    # Public-facing studio identity & contact fields
    # These mirror the artist profile fields but are tailored for studios.
    name = Column(String, nullable=True)
    slug = Column(String, nullable=True, unique=True, index=True)
    about = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    address = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    telegram = Column(String, nullable=True)
    vk = Column(String, nullable=True)
    session_price_label = Column(String, nullable=True)

    # Per-role onboarding flag – separate from the global user.onboarding_completed
    onboarding_completed = Column(Boolean, default=False, nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="studio")

    # Residents (artists that belong to this studio)
    residents = relationship(
        "ArtistStudioResident",
        back_populates="studio",
        cascade="all, delete-orphan",
    )

    # Booking requests submitted for this studio
    booking_requests = relationship(
        "BookingRequest",
        back_populates="studio",
        cascade="all, delete-orphan",
    )
