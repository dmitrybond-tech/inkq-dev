"""Portfolio image model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class PortfolioImage(Base):
    """Portfolio image model for storing user portfolio/wannado images."""
    
    __tablename__ = "portfolio_images"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String, nullable=False, default="portfolio")  # "portfolio" or "wannado"
    url = Column(String, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)

    # Optional metadata fields for per-image details (editable from dashboard)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    approx_price = Column(String, nullable=True)
    placement = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship back to User
    user = relationship("User", back_populates="portfolio_images")

