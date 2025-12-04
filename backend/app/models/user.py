"""User model."""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base


class AccountType(str, enum.Enum):
    """Account type enumeration."""
    ARTIST = "artist"
    STUDIO = "studio"
    MODEL = "model"


class User(Base):
    """User model representing accounts in the system."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 1-1 relationships with role entities
    artist = relationship("Artist", back_populates="user", uselist=False)
    studio = relationship("Studio", back_populates="user", uselist=False)
    model = relationship("Model", back_populates="user", uselist=False)
    
    # Sessions relationship
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    
    # Media fields
    avatar_url = Column(String, nullable=True)
    banner_url = Column(String, nullable=True)
    
    # Portfolio images relationship
    portfolio_images = relationship("PortfolioImage", back_populates="user", cascade="all, delete-orphan")

