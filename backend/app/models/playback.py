from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Session, synonym
from app.db.base import Base
from app.utils.helpers import utc_now

class PlaybackEvent(Base):
    __tablename__ = "playback_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    song_id = Column(Integer, ForeignKey("library_songs.id"), nullable=False, index=True)
    event_type = Column(String(20), nullable=False)  # play, skip, complete
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    timestamp = Column("occurred_at", DateTime(timezone=True), nullable=False, default=utc_now)
    occurred_at = synonym("timestamp")
    location = Column(String(120), nullable=True)
    completed_ratio = Column(Float, nullable=False, default=0.0)
    played_seconds = Column(Float, nullable=False, default=0.0)
    is_looped = Column(Boolean, nullable=False, default=False)
    skipped = Column(Boolean, nullable=False, default=False)
    weight = Column(Float, nullable=False, default=1.0)

    user = relationship("User", back_populates="playback_events")
    song = relationship("LibrarySong", back_populates="playback_events")
    session = relationship("PlaybackSession", back_populates="playback_events")

class UserPlaybackLog(Base):
    __tablename__ = "user_playback_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    song_id = Column(Integer, ForeignKey("library_songs.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=utc_now)

def create_event(db: Session, user_id: int, data):
    event = PlaybackEvent(
        user_id=user_id,
        song_id=data.song_id,
        event_type=data.event_type,
        session_id=data.session_id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def get_user_recent_events(db: Session, user_id: int, limit=50):
    return (
        db.query(PlaybackEvent)
        .filter(PlaybackEvent.user_id == user_id)
        .order_by(PlaybackEvent.timestamp.desc())
        .limit(limit)
        .all()
    )
