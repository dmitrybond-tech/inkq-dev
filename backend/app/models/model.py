"""Model role model."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class Model(Base):
    """Model role model - 1-1 with User."""

    __tablename__ = "models"

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

    # Optional display name and slug/username for public pages
    display_name = Column(String, nullable=True)
    slug = Column(String, unique=True, index=True, nullable=True)

    # Profile metadata
    about = Column(Text, nullable=True)
    # Store style IDs as JSON array of strings
    styles = Column(JSONB, nullable=False, default=list)
    city = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    telegram = Column(String, nullable=True)

    # Optional links to shared media records (portfolio_images)
    profile_image_id = Column(Integer, ForeignKey("portfolio_images.id"), nullable=True)
    banner_image_id = Column(Integer, ForeignKey("portfolio_images.id"), nullable=True)

    # Relationship back to User
    user = relationship("User", back_populates="model")

    # Gallery items
    gallery_items = relationship(
        "ModelGalleryItem",
        back_populates="model",
        cascade="all, delete-orphan",
    )
