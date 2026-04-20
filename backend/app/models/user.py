from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.utils.helpers import utc_now


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True, index=True)
    device_class = Column(String(20), nullable=False, default="standard")
    taste_vector = Column(JSON, nullable=True)
    is_telegram_user = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    subscriptions = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    listings = relationship("PlaylistMarketplace", back_populates="seller")
    purchases = relationship("PlaylistPurchase", back_populates="buyer")
    song_listings = relationship("SongMarketplace", back_populates="seller")
    song_purchases = relationship("SongPurchase", back_populates="buyer")
    playback_events = relationship("PlaybackEvent", back_populates="user")
    playlist_saves = relationship("UserPlaylistSave", back_populates="user")
    listening_sessions = relationship("PlaybackSession", back_populates="user")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="expired")
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="subscriptions")
