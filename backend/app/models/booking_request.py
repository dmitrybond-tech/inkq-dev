"""Booking request model for studio bookings."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class BookingRequest(Base):
    """Booking request for a studio, optionally for a specific artist."""

    __tablename__ = "booking_requests"

    id = Column(Integer, primary_key=True, index=True)
    studio_id = Column(Integer, ForeignKey("studios.id"), nullable=False, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=True, index=True)

    # "general" | "artist_specific"
    type = Column(String, nullable=False)

    client_name = Column(String, nullable=False)
    client_contact = Column(String, nullable=False)
    comment = Column(Text, nullable=True)

    # "new" | "in_progress" | "closed"
    status = Column(String, nullable=False, default="new")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    studio = relationship("Studio", back_populates="booking_requests")
    artist = relationship("Artist", back_populates="booking_requests")


