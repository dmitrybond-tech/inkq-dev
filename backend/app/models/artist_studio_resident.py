"""Artist-studio resident relationship model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class ArtistStudioResident(Base):
    """Link table between studios and artists with invitation status."""

    __tablename__ = "artist_studio_residents"
    __table_args__ = (
        UniqueConstraint("studio_id", "artist_id", name="uq_studio_artist_resident"),
    )

    id = Column(Integer, primary_key=True, index=True)
    studio_id = Column(Integer, ForeignKey("studios.id"), nullable=False, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False, index=True)
    status = Column(
        String,
        nullable=False,
        default="invited",  # invited | accepted | rejected
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    studio = relationship("Studio", back_populates="residents")
    artist = relationship("Artist", back_populates="studio_residencies")


