"""
Playback Session Service
Manages user playback sessions, concurrent stream limits, and session lifecycle
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import uuid

from app.models.stream_session import StreamSession
from app.models.user import User


class PlaybackSessionService:
    """Manage playback sessions and enforce concurrent stream limits"""
    
    CONCURRENT_LIMITS = {
        "free": 1,
        "premium": 2,
        "premium_plus": 4,
    }
    
    SESSION_TIMEOUT = timedelta(hours=4)
    HEARTBEAT_TIMEOUT = timedelta(minutes=2)  # Sessions without heartbeat are stale
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_stream_start(
        self,
        user_id: str,
        device_id: str
    ) -> Dict[str, Any]:
        """
        Check if user can start a new stream based on concurrent limits.
        
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "max_streams": int,
                "active_count": int
            }
        """
        # Get user's subscription tier
        user = self.db.query(User).filter_by(id=int(user_id)).first()
        tier = user.subscription_tier if user and hasattr(user, 'subscription_tier') else "free"
        
        max_streams = self.CONCURRENT_LIMITS.get(tier, 1)
        
        # Count active sessions for this user
        cutoff = datetime.utcnow() - self.HEARTBEAT_TIMEOUT
        active_count = self.db.query(StreamSession).filter(
            StreamSession.user_id == int(user_id),
            StreamSession.is_active == True,
            StreamSession.ended_at.is_(None),
            StreamSession.expires_at > datetime.utcnow(),
            StreamSession.last_heartbeat_at > cutoff
        ).count()
        
        if active_count >= max_streams:
            return {
                "allowed": False,
                "reason": f"Maximum {max_streams} concurrent stream(s) reached",
                "max_streams": max_streams,
                "active_count": active_count
            }
        
        return {
            "allowed": True,
            "reason": "Stream allowed",
            "max_streams": max_streams,
            "active_count": active_count
        }
    
    def create_session(
        self,
        user_id: str,
        device_id: str,
        song_id: str,
        audio_quality: str,
        bitrate: int
    ) -> StreamSession:
        """Create a new playback session"""
        # Generate unique session ID
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        
        session = StreamSession(
            id=session_id,
            user_id=int(user_id),
            device_id=device_id,
            song_id=song_id,
            audio_quality=audio_quality,
            bitrate=bitrate,
            started_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.SESSION_TIMEOUT,
            is_active=True,
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[StreamSession]:
        """Get a session by ID, checking it's not expired"""
        session = self.db.query(StreamSession).filter_by(id=session_id).first()
        
        if not session:
            return None
        
        # Check if session is expired
        if session.is_expired():
            return None
        
        # Check heartbeat timeout
        if session.last_heartbeat_at:
            cutoff = datetime.utcnow() - self.HEARTBEAT_TIMEOUT
            if session.last_heartbeat_at < cutoff:
                # Session is stale, mark as ended
                session.end_session()
                self.db.commit()
                return None
        
        return session
    
    def update_heartbeat(self, session_id: str, user_id: int, position_ms: int) -> bool:
        """Update session heartbeat with current playback position"""
        session = self.get_session(session_id)
        
        if not session:
            return False
        if session.user_id != int(user_id):
            return False
        
        session.touch_heartbeat(position_ms)
        self.db.commit()
        
        return True
    
    def end_session(self, session_id: str, user_id: int) -> bool:
        """End a playback session"""
        session = self.db.query(StreamSession).filter_by(id=session_id).first()
        
        if not session:
            return False
        if session.user_id != int(user_id):
            return False
        
        session.end_session()
        self.db.commit()
        
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """Remove sessions older than timeout"""
        cutoff = datetime.utcnow() - self.SESSION_TIMEOUT
        
        # Find expired sessions that haven't been marked as ended
        expired = self.db.query(StreamSession).filter(
            StreamSession.is_active == True,
            StreamSession.ended_at.is_(None),
            StreamSession.expires_at < cutoff
        ).all()
        
        count = 0
        for session in expired:
            session.end_session()
            count += 1
        
        self.db.commit()
        return count
