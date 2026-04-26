"""
Song access control models for payment-based playback
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class SongAccess(Base):
    """Tracks which users have access to which songs"""
    __tablename__ = "song_access"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    song_id = Column(String(36), ForeignKey("library_songs.id"), nullable=False, index=True)
    
    # Access type: purchase, subscription, free, promo
    access_type = Column(String(20), nullable=False, default="purchase")
    
    # For purchases
    purchase_id = Column(String(36), ForeignKey("payments.id"), nullable=True)
    purchase_price = Column(Float, nullable=True)
    
    # For subscriptions
    subscription_id = Column(String(36), nullable=True)
    
    # Access validity
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)  # NULL = permanent
    
    # Usage tracking
    play_count = Column(Integer, default=0)
    last_played_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Table args for composite index
    __table_args__ = (
        Index('idx_song_access_user_song_active', 'user_id', 'song_id', 'is_active'),
    )


class SongPricing(Base):
    """Pricing information for songs"""
    __tablename__ = "song_pricing"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    song_id = Column(String(36), ForeignKey("library_songs.id"), unique=True, nullable=False)
    
    # Pricing options
    is_free = Column(Boolean, default=False)
    individual_price = Column(Float, nullable=True)  # USD
    
    # Subscription requirements
    requires_premium = Column(Boolean, default=False)
    
    # Promotional pricing
    promo_price = Column(Float, nullable=True)
    promo_ends_at = Column(DateTime, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
