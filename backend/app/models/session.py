from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.utils.helpers import utc_now


class PlaybackSession(Base):
    """Represents a user's contiguous listening session."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    status = Column(String(20), nullable=False, default="active")

    user = relationship("User", back_populates="listening_sessions")
    playback_events = relationship("PlaybackEvent", back_populates="session")
    recommendation_events = relationship(
        "SessionRecommendationEvent",
        back_populates="session",
    )


class SessionRecommendationEvent(Base):
    __tablename__ = "session_recommendation_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    song_id = Column(String(255), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    score = Column(Float, nullable=False, default=0.0)
    accepted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    session = relationship("PlaybackSession", back_populates="recommendation_events")


ListeningSession = PlaybackSession
Session = PlaybackSession
