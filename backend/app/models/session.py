"""Session model for authentication."""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Session(Base):
    """Session model for storing authentication tokens."""
    
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, index=True)  # Opaque token
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Relationship to User
    user = relationship("User", back_populates="sessions")

