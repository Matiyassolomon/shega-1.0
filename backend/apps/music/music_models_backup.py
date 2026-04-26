from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.db import Base


def utc_now():
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True, index=True)
    device_class = Column(String(20), nullable=False, default="standard")
    taste_vector = Column(JSON, nullable=True)  # Stores aggregated music preferences
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


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="expired")
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="subscriptions")


class PremiumContent(Base):
    __tablename__ = "premium_content"

    id = Column(Integer, primary_key=True, index=True)
    navidrome_song_id = Column(String, nullable=False, unique=True, index=True)
    requires_subscription = Column(Boolean, nullable=False, default=True)


class PlaylistMarketplace(Base):
    __tablename__ = "playlist_marketplace"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(String, nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="ETB")
    sales_count = Column(Integer, nullable=False, default=0)
    is_public = Column(Boolean, nullable=False, default=True)

    seller = relationship("User", back_populates="listings")
    purchases = relationship("PlaylistPurchase", back_populates="listing")


class PlaylistPurchase(Base):
    __tablename__ = "playlist_purchases"

    id = Column(Integer, primary_key=True, index=True)
    playlist_listing_id = Column(
        Integer, ForeignKey("playlist_marketplace.id"), nullable=False, index=True
    )
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    listing = relationship("PlaylistMarketplace", back_populates="purchases")
    buyer = relationship("User", back_populates="purchases")


class SongMarketplace(Base):
    __tablename__ = "song_marketplace"

    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(String(255), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="ETB")
    sales_count = Column(Integer, nullable=False, default=0)
    is_public = Column(Boolean, nullable=False, default=True)

    seller = relationship("User", back_populates="song_listings")
    purchases = relationship("SongPurchase", back_populates="listing")


class SongPurchase(Base):
    __tablename__ = "song_purchases"

    id = Column(Integer, primary_key=True, index=True)
    song_listing_id = Column(
        Integer, ForeignKey("song_marketplace.id"), nullable=False, index=True
    )
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    listing = relationship("SongMarketplace", back_populates="purchases")
    buyer = relationship("User", back_populates="song_purchases")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    method = Column(String(20), nullable=False)
    payment_type = Column(String(50), nullable=True)
    playlist_id = Column(String(255), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    user = relationship("User", back_populates="payments")


class HolidayRule(Base):
    __tablename__ = "holiday_rules"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    eth_month = Column(Integer, nullable=False)
    eth_day = Column(Integer, nullable=False)
    recommendations = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class MusicMetadata(Base):
    __tablename__ = "music_metadata"

    id = Column(Integer, primary_key=True, index=True)
    artist = Column(String(255), nullable=True, index=True)
    genre = Column(String(100), nullable=False, default="Ethiopian Music")
    qenet_mode = Column(String(50), nullable=False, index=True)
    tempo = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    filename = Column(String(255), nullable=False)
    extracted_features = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class UserPlaybackLog(Base):
    __tablename__ = "user_playback_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    music_id = Column(
        Integer, ForeignKey("music_metadata.id"), nullable=False, index=True
    )
    played_seconds = Column(Float, nullable=False, default=0.0)
    skipped = Column(Boolean, nullable=False, default=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class LibrarySong(Base):
    __tablename__ = "library_songs"

    id = Column(Integer, primary_key=True, index=True)
    navidrome_song_id = Column(String(255), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False, index=True)
    genre = Column(String(100), nullable=False, default="Unknown")
    country = Column(String(100), nullable=True, index=True)
    language = Column(String(100), nullable=True)
    qenet_mode = Column(String(50), nullable=True, index=True)
    release_date = Column(String(20), nullable=True)
    tempo = Column(Float, nullable=False, default=0.0)
    duration = Column(Float, nullable=False, default=0.0)
    extracted_features = Column(JSON, nullable=False, default=dict)
    playlist_id = Column(String(255), nullable=True, index=True)
    play_count_7d = Column(Integer, nullable=False, default=0)
    like_count_7d = Column(Integer, nullable=False, default=0)
    skip_rate = Column(Float, nullable=False, default=0.0)
    cover_art_path = Column(String(255), nullable=True)
    stream_path = Column(String(255), nullable=True)
    is_premium = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    playback_events = relationship("PlaybackEvent", back_populates="song")


class PlaybackEvent(Base):
    __tablename__ = "playback_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    song_id = Column(
        Integer,
        ForeignKey("library_songs.id"),
        nullable=False,
        index=True,
    )
    location = Column(String(100), nullable=True, index=True)
    completed_ratio = Column(Float, nullable=False, default=0.0)
    played_seconds = Column(Float, nullable=False, default=0.0)
    is_looped = Column(Boolean, nullable=False, default=False)
    skipped = Column(Boolean, nullable=False, default=False)
    weight = Column(Float, nullable=False, default=1.0)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    user = relationship("User", back_populates="playback_events")
    song = relationship("LibrarySong", back_populates="playback_events")


class PlaylistSocialSignal(Base):
    __tablename__ = "playlist_social_signals"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(String(255), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    creator_name = Column(String(255), nullable=False)
    artist_name = Column(String(255), nullable=True)
    artist_verified = Column(Boolean, nullable=False, default=False)
    save_count = Column(Integer, nullable=False, default=0)
    share_count = Column(Integer, nullable=False, default=0)
    region = Column(String(100), nullable=True, index=True)
    preview_song_id = Column(String(255), nullable=True)
    cover_art_path = Column(String(255), nullable=True)
    internal_stream_path = Column(String(255), nullable=True)
    internal_art_path = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class UserPlaylistSave(Base):
    __tablename__ = "user_playlist_saves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    playlist_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    user = relationship("User", back_populates="playlist_saves")
