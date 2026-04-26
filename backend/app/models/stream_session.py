"""
Stream Session Model
Tracks individual active playback sessions for stream proxying.
This is separate from PlaybackSession which tracks listening sessions.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.db.base import Base
from app.utils.helpers import utc_now


class StreamSession(Base):
    """
    Represents an active song playback session.
    
    Created when /playback/start returns a PLAYING response.
    Used by /playback/stream/{session_id} to validate and proxy streams.
    Tracks heartbeats and enforces concurrent stream limits.
    """
    
    __tablename__ = "stream_sessions"
    
    # Primary key - this is the session_id used in URLs
    id = Column(String(255), primary_key=True, index=True)
    
    # User and device
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(255), nullable=False, index=True)
    
    # Song being played
    song_id = Column(String(255), nullable=False, index=True)
    
    # Audio quality settings
    audio_quality = Column(String(20), nullable=False, default="high")
    bitrate = Column(Integer, nullable=False, default=320)
    
    # Session lifecycle
    started_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Heartbeat tracking
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    current_position_ms = Column(Integer, nullable=True, default=0)
    
    # Session status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="stream_sessions")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set expiration if not provided (4 hours default)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=4)
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        if self.ended_at:
            return True
        if datetime.utcnow() > self.expires_at:
            return True
        return False
    
    def touch_heartbeat(self, position_ms: int = None):
        """Update heartbeat timestamp and position"""
        self.last_heartbeat_at = utc_now()
        if position_ms is not None:
            self.current_position_ms = position_ms
    
    def end_session(self):
        """Mark session as ended"""
        self.ended_at = utc_now()
        self.is_active = False


# Update User model relationship
# Add to app/models/user.py:
# stream_sessions = relationship("StreamSession", back_populates="user")
