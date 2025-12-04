"""Model gallery item model."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class ModelGalleryItem(Base):
    """Gallery item for a model profile."""

    __tablename__ = "model_gallery_items"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(
        Integer,
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # FK into shared media table (portfolio_images)
    image_id = Column(
        Integer,
        ForeignKey("portfolio_images.id"),
        nullable=False,
        index=True,
    )
    caption = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    model = relationship("Model", back_populates="gallery_items")
    image = relationship("PortfolioImage")


