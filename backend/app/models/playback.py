from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.utils.helpers import utc_now


class UserPlaybackLog(Base):
    __tablename__ = "user_playback_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    music_id = Column(Integer, ForeignKey("music_metadata.id"), nullable=False, index=True)
    played_seconds = Column(Float, nullable=False, default=0.0)
    skipped = Column(Boolean, nullable=False, default=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class PlaybackEvent(Base):
    __tablename__ = "playback_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    song_id = Column(Integer, ForeignKey("library_songs.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    event_type = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    location = Column(String(100), nullable=True, index=True)
    completed_ratio = Column(Float, nullable=False, default=0.0)
    played_seconds = Column(Float, nullable=False, default=0.0)
    is_looped = Column(Boolean, nullable=False, default=False)
    skipped = Column(Boolean, nullable=False, default=False)
    weight = Column(Float, nullable=False, default=1.0)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    user = relationship("User", back_populates="playback_events")
    song = relationship("LibrarySong", back_populates="playback_events")
    session = relationship("PlaybackSession", back_populates="playback_events")
