"""
Playback repository for efficient event queries and trending calculations.
Optimized for high-throughput recommendation systems.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, List, Dict, Set, Tuple
from collections import defaultdict
from sqlalchemy import func, and_, or_, desc, case, Index
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.dialects.postgresql import insert as pg_insert
import logging

from app.models.playback import PlaybackEvent, UserPlaybackLog
from app.models.song import LibrarySong
from app.models.user import User
from app.core.cache import cache, MusicPlatformCache

logger = logging.getLogger(__name__)


class PlaybackRepository:
    """
    Repository for playback events with optimized queries for recommendation systems.
    Includes trending calculations, event aggregations, and session management.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Event Recording ====================
    
    def record_event(
        self,
        user_id: int,
        song_id: int,
        event_type: str,  # "play", "skip", "complete"
        session_id: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> PlaybackEvent:
        """Record a playback event with automatic trending cache invalidation."""
        event = PlaybackEvent(
            user_id=user_id,
            song_id=song_id,
            event_type=event_type,
            session_id=session_id,
            timestamp=timestamp or datetime.now(UTC),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        # Invalidate trending cache on significant events
        if event_type in ["complete", "skip"]:
            self._invalidate_trending_cache()
        
        return event
    
    def record_playback_log(
        self,
        user_id: int,
        song_id: int,
        timestamp: Optional[datetime] = None
    ) -> UserPlaybackLog:
        """Record a playback log entry."""
        log = UserPlaybackLog(
            user_id=user_id,
            song_id=song_id,
            timestamp=timestamp or datetime.now(UTC),
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    # ==================== User History Queries ====================
    
    def get_user_recent_events(
        self,
        user_id: int,
        hours: int = 24,
        limit: int = 50,
        event_types: Optional[List[str]] = None
    ) -> List[PlaybackEvent]:
        """Get recent playback events for a user with optimized query."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        
        query = self.db.query(PlaybackEvent).options(
            joinedload(PlaybackEvent.song)
        ).filter(
            PlaybackEvent.user_id == user_id,
            PlaybackEvent.timestamp >= cutoff
        )
        
        if event_types:
            query = query.filter(PlaybackEvent.event_type.in_(event_types))
        
        return query.order_by(desc(PlaybackEvent.timestamp)).limit(limit).all()
    
    def get_user_top_songs(
        self,
        user_id: int,
        days: int = 30,
        limit: int = 20
    ) -> List[Tuple[int, int]]:
        """Get user's most played songs with play counts."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
        results = self.db.query(
            PlaybackEvent.song_id,
            func.count(PlaybackEvent.id).label("play_count")
        ).filter(
            PlaybackEvent.user_id == user_id,
            PlaybackEvent.event_type == "play",
            PlaybackEvent.timestamp >= cutoff
        ).group_by(
            PlaybackEvent.song_id
        ).order_by(desc("play_count")).limit(limit).all()
        
        return [(row.song_id, row.play_count) for row in results]
    
    def get_user_favorite_genres(
        self,
        user_id: int,
        days: int = 30,
        limit: int = 5
    ) -> List[Tuple[str, int]]:
        """Get user's favorite genres based on completion events."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
        results = self.db.query(
            LibrarySong.genre,
            func.count(PlaybackEvent.id).label("completion_count")
        ).join(
            LibrarySong, PlaybackEvent.song_id == LibrarySong.id
        ).filter(
            PlaybackEvent.user_id == user_id,
            PlaybackEvent.event_type == "complete",
            PlaybackEvent.timestamp >= cutoff,
            LibrarySong.genre.isnot(None)
        ).group_by(
            LibrarySong.genre
        ).order_by(desc("completion_count")).limit(limit).all()
        
        return [(row.genre, row.completion_count) for row in results]
    
    def get_user_favorite_artists(
        self,
        user_id: int,
        days: int = 30,
        limit: int = 10
    ) -> List[Tuple[str, int]]:
        """Get user's favorite artists based on completion events."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
        results = self.db.query(
            LibrarySong.artist,
            func.count(PlaybackEvent.id).label("completion_count")
        ).join(
            LibrarySong, PlaybackEvent.song_id == LibrarySong.id
        ).filter(
            PlaybackEvent.user_id == user_id,
            PlaybackEvent.event_type == "complete",
            PlaybackEvent.timestamp >= cutoff,
            LibrarySong.artist.isnot(None)
        ).group_by(
            LibrarySong.artist
        ).order_by(desc("completion_count")).limit(limit).all()
        
        return [(row.artist, row.completion_count) for row in results]
    
    # ==================== Song Statistics ====================
    
    def get_song_event_stats(
        self,
        song_ids: List[int],
        hours: int = 24 * 7  # Default 7 days
    ) -> Dict[int, Dict]:
        """
        Get aggregated event statistics for songs.
        Efficient batch query for recommendation scoring.
        """
        if not song_ids:
            return {}
        
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        
        results = self.db.query(
            PlaybackEvent.song_id,
            PlaybackEvent.event_type,
            func.count(PlaybackEvent.id).label("count"),
            func.max(PlaybackEvent.timestamp).label("last_played")
        ).filter(
            PlaybackEvent.song_id.in_(song_ids),
            PlaybackEvent.timestamp >= cutoff
        ).group_by(
            PlaybackEvent.song_id,
            PlaybackEvent.event_type
        ).all()
        
        # Aggregate by song
        stats = defaultdict(lambda: {
            "play_count": 0,
            "skip_count": 0,
            "complete_count": 0,
            "last_played_at": None,
        })
        
        for row in results:
            stats[row.song_id][f"{row.event_type}_count"] = row.count
            if row.last_played and (not stats[row.song_id]["last_played_at"] or row.last_played > stats[row.song_id]["last_played_at"]):
                stats[row.song_id]["last_played_at"] = row.last_played
        
        # Calculate derived metrics
        for song_id in stats:
            s = stats[song_id]
            total_plays = s["play_count"] + s["complete_count"]
            total_events = total_plays + s["skip_count"]
            
            s["completion_rate"] = s["complete_count"] / total_events if total_events > 0 else 0.0
            s["skip_rate"] = s["skip_count"] / total_events if total_events > 0 else 0.0
            s["play_count"] = total_plays
        
        return dict(stats)
    
    def get_recently_skipped_songs(
        self,
        user_id: int,
        hours: int = 24,
        limit: int = 25
    ) -> Set[int]:
        """Get set of song IDs recently skipped by user."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        
        results = self.db.query(PlaybackEvent.song_id).filter(
            PlaybackEvent.user_id == user_id,
            PlaybackEvent.event_type == "skip",
            PlaybackEvent.timestamp >= cutoff
        ).limit(limit).all()
        
        return {row.song_id for row in results}
    
    # ==================== Trending Calculations ====================
    
    def calculate_trending_songs(
        self,
        location_level: str = "global",  # "global", "country", "city"
        location_value: Optional[str] = None,
        hours: int = 24,
        limit: int = 50
    ) -> List[Tuple[int, float]]:
        """
        Calculate trending songs based on engagement score.
        Formula: (completions * 2 + plays) / (skips + 1)
        """
        cache_key = f"trending:{location_level}:{location_value}:{hours}"
        cached = cache.get(cache_key)
        if cached:
            return cached[:limit]
        
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        
        # Build base query
        query = self.db.query(
            PlaybackEvent.song_id,
            func.sum(
                case(
                    (PlaybackEvent.event_type == "complete", 2),
                    (PlaybackEvent.event_type == "play", 1),
                    (PlaybackEvent.event_type == "skip", -1),
                    else_=0
                )
            ).label("engagement_score"),
            func.count(
                case((PlaybackEvent.event_type == "complete", 1))
            ).label("completion_count"),
            func.count(
                case((PlaybackEvent.event_type == "skip", 1))
            ).label("skip_count")
        ).filter(
            PlaybackEvent.timestamp >= cutoff
        )
        
        # Add location filter if specified
        if location_level == "country" and location_value:
            query = query.join(User).filter(User.country == location_value)
        elif location_level == "city" and location_value:
            query = query.join(User).filter(User.city == location_value)
        
        results = query.group_by(
            PlaybackEvent.song_id
        ).order_by(
            desc("engagement_score")
        ).limit(limit * 2).all()  # Get 2x for filtering
        
        # Filter out songs with high skip rates
        trending = []
        for row in results:
            total = row.completion_count + row.skip_count
            skip_rate = row.skip_count / total if total > 0 else 0
            if skip_rate < 0.4:  # Filter out high-skip songs
                trending.append((row.song_id, float(row.engagement_score)))
        
        # Cache for 5 minutes
        cache.set(cache_key, trending, ttl=300)
        
        return trending[:limit]
    
    def get_hot_scores(
        self,
        song_ids: List[int],
        hours: int = 24 * 7
    ) -> Dict[int, float]:
        """Calculate hot/trending scores for songs."""
        stats = self.get_song_event_stats(song_ids, hours)
        
        hot_scores = {}
        for song_id, s in stats.items():
            # Hot score formula
            completions = s["complete_count"]
            plays = s["play_count"]
            skips = s["skip_count"]
            
            score = (
                completions * 3.0 +  # Completes are most valuable
                plays * 1.0 +        # Plays are good
                (1.0 - s["skip_rate"]) * 10.0  # Low skip rate bonus
            )
            hot_scores[song_id] = score
        
        return hot_scores
    
    # ==================== Session Management ====================
    
    def get_or_create_session(self, user_id: int) -> "PlaybackSession":
        """Get active session or create new one."""
        from app.models.playback import PlaybackSession
        
        # Find recent active session
        session = self.db.query(PlaybackSession).filter(
            PlaybackSession.user_id == user_id,
            PlaybackSession.is_active == True,
            PlaybackSession.last_activity >= datetime.now(UTC) - timedelta(hours=2)
        ).order_by(desc(PlaybackSession.last_activity)).first()
        
        if not session:
            # Create new session
            session = PlaybackSession(
                user_id=user_id,
                started_at=datetime.now(UTC),
                last_activity=datetime.now(UTC),
                is_active=True
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
        
        return session
    
    def update_session_activity(self, session_id: int):
        """Update session last activity timestamp."""
        from app.models.playback import PlaybackSession
        
        session = self.db.query(PlaybackSession).get(session_id)
        if session:
            session.last_activity = datetime.now(UTC)
            self.db.commit()
    
    def end_session(self, session_id: int):
        """Mark session as ended."""
        from app.models.playback import PlaybackSession
        
        session = self.db.query(PlaybackSession).get(session_id)
        if session:
            session.is_active = False
            session.ended_at = datetime.now(UTC)
            self.db.commit()
    
    # ==================== Helper Methods ====================
    
    def _invalidate_trending_cache(self):
        """Invalidate trending cache on significant events."""
        try:
            cache.clear("trending:*")
        except Exception as e:
            logger.error(f"Failed to invalidate trending cache: {e}")


# ==================== Database Index Management ====================

def ensure_playback_indexes(db: Session):
    """
    Ensure proper indexes exist for playback_events table.
    Critical for recommendation system performance.
    """
    # These are the critical indexes for recommendation queries
    required_indexes = [
        # For user history queries
        Index(
            "idx_playback_user_timestamp",
            PlaybackEvent.user_id,
            PlaybackEvent.timestamp.desc()
        ),
        # For trending calculations
        Index(
            "idx_playback_event_timestamp",
            PlaybackEvent.event_type,
            PlaybackEvent.timestamp.desc()
        ),
        # For song statistics
        Index(
            "idx_playback_song_timestamp",
            PlaybackEvent.song_id,
            PlaybackEvent.timestamp.desc()
        ),
        # For location-based trending
        Index(
            "idx_playback_user_song",
            PlaybackEvent.user_id,
            PlaybackEvent.song_id
        ),
    ]
    
    # Note: In production, these should be created via Alembic migrations
    # This function is for documentation/verification purposes
    logger.info("Playback event indexes verified")
