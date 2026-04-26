"""
Enhanced 4-Layer Recommendation Engine with YouTube Integration.

Architecture:
    Layer 1: Candidate Generation (User history + Trending + YouTube + Random)
    Layer 2: Ranking Engine (Scoring with YouTube boost)
    Layer 3: Session Optimization (Diversity + No repeats)
    Layer 4: Exploration vs Exploitation (80/20 split)

YouTube Integration: 20% weight maximum
Internal Signals: 80% weight
"""

from __future__ import annotations
import random
import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from math import exp

from sqlalchemy import func, or_, desc
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.core.settings import get_settings
from app.core.cache import cache, MusicPlatformCache
from app.repositories.recommendation_repo import RecommendationRepository
from app.services.youtube_integration import youtube_service, YouTubeBoostResult

logger = logging.getLogger(__name__)


@dataclass
class RankedSong:
    """Song with ranking information."""
    song: models.LibrarySong
    base_score: float
    final_score: float
    reasons: List[str]
    breakdown: schemas.RecommendationBreakdown
    source: str = "internal"  # "internal", "youtube", "exploration"
    youtube_boost: float = 0.0


@dataclass 
class CandidatePool:
    """Collection of candidate songs from various sources."""
    from_history: List[models.LibrarySong] = field(default_factory=list)
    from_genre: List[models.LibrarySong] = field(default_factory=list)
    from_artist: List[models.LibrarySong] = field(default_factory=list)
    from_trending: List[models.LibrarySong] = field(default_factory=list)
    from_youtube: List[models.LibrarySong] = field(default_factory=list)
    from_random: List[models.LibrarySong] = field(default_factory=list)


# ============================================================================
# LAYER 1: CANDIDATE GENERATION
# ============================================================================

class CandidateGenerationLayer:
    """
    Layer 1: Generate diverse candidate set from multiple sources.
    
    Sources:
    - User listening history (30 songs)
    - Same genre as recent plays (40 songs)
    - Same artist as recent plays (20 songs)
    - Internal trending (25 songs)
    - YouTube trending (15 songs) - External signal
    - Random exploration (10 songs)
    """
    
    def __init__(self, repository: RecommendationRepository, db: Session):
        self.repository = repository
        self.db = db
    
    def generate_candidates(
        self,
        user_id: int,
        current_song_id: Optional[str] = None,
        location: Optional[str] = None,
        include_youtube: bool = True
    ) -> CandidatePool:
        """Generate candidates from all sources."""
        pool = CandidatePool()
        
        # 1. User History (Personalization)
        pool.from_history = self._get_from_user_history(user_id, limit=30)
        
        # 2. Genre Matches (Discovery)
        recent_genres = self._get_recent_genres(user_id)
        if recent_genres:
            pool.from_genre = self._get_from_genres(recent_genres, exclude_user_id=user_id, limit=40)
        
        # 3. Artist Matches (Fan base)
        recent_artists = self._get_recent_artists(user_id)
        if recent_artists:
            pool.from_artist = self._get_from_artists(recent_artists, exclude_user_id=user_id, limit=20)
        
        # 4. Internal Trending (Popularity)
        pool.from_trending = self._get_from_trending(location=location, limit=25)
        
        # 5. YouTube Trending (External Signal - 20% max)
        if include_youtube and youtube_service.enabled:
            pool.from_youtube = self._get_from_youtube_trending(limit=15)
        
        # 6. Random Exploration (Diversity)
        pool.from_random = self._get_random_candidates(exclude_user_id=user_id, limit=10)
        
        logger.info(
            f"Candidate pool for user {user_id}: "
            f"history={len(pool.from_history)}, "
            f"genre={len(pool.from_genre)}, "
            f"artist={len(pool.from_artist)}, "
            f"trending={len(pool.from_trending)}, "
            f"youtube={len(pool.from_youtube)}, "
            f"random={len(pool.from_random)}"
        )
        
        return pool
    
    def _get_from_user_history(self, user_id: int, limit: int) -> List[models.LibrarySong]:
        """Get songs from user's recent completions."""
        recent_events = self.repository.playback.get_user_recent_events(
            user_id, hours=168, limit=50, event_types=["complete"]
        )
        
        song_ids = list({event.song_id for event in recent_events})[:limit]
        if not song_ids:
            return []
        
        songs = (
            self.db.query(models.LibrarySong)
            .filter(models.LibrarySong.id.in_(song_ids))
            .all()
        )
        return songs
    
    def _get_recent_genres(self, user_id: int, limit: int = 5) -> List[str]:
        """Get user's recently listened genres."""
        genres = self.repository.playback.get_user_favorite_genres(
            user_id, days=30, limit=limit
        )
        return [g[0] for g in genres if g[0]]
    
    def _get_from_genres(
        self,
        genres: List[str],
        exclude_user_id: int,
        limit: int
    ) -> List[models.LibrarySong]:
        """Get popular songs from specified genres."""
        return (
            self.db.query(models.LibrarySong)
            .filter(
                models.LibrarySong.genre.in_(genres),
                ~models.LibrarySong.id.in_(
                    self._get_user_song_ids(exclude_user_id)
                )
            )
            .order_by(desc(models.LibrarySong.play_count_7d))
            .limit(limit)
            .all()
        )
    
    def _get_recent_artists(self, user_id: int, limit: int = 5) -> List[str]:
        """Get user's recently listened artists."""
        artists = self.repository.playback.get_user_favorite_artists(
            user_id, days=30, limit=limit
        )
        return [a[0] for a in artists if a[0]]
    
    def _get_from_artists(
        self,
        artists: List[str],
        exclude_user_id: int,
        limit: int
    ) -> List[models.LibrarySong]:
        """Get songs from specified artists."""
        return (
            self.db.query(models.LibrarySong)
            .filter(
                models.LibrarySong.artist.in_(artists),
                ~models.LibrarySong.id.in_(
                    self._get_user_song_ids(exclude_user_id)
                )
            )
            .order_by(desc(models.LibrarySong.play_count_7d))
            .limit(limit)
            .all()
        )
    
    def _get_from_trending(
        self,
        location: Optional[str],
        limit: int
    ) -> List[models.LibrarySong]:
        """Get internal trending songs."""
        trending = self.repository.playback.calculate_trending_songs(
            location_level="global",
            hours=24,
            limit=limit
        )
        
        if not trending:
            return []
        
        song_ids = [t[0] for t in trending]
        songs = (
            self.db.query(models.LibrarySong)
            .filter(models.LibrarySong.id.in_(song_ids))
            .all()
        )
        
        # Sort by trending order
        song_map = {s.id: s for s in songs}
        return [song_map[sid] for sid in song_ids if sid in song_map]
    
    def _get_from_youtube_trending(self, limit: int) -> List[models.LibrarySong]:
        """Match internal songs to YouTube trending."""
        # Get YouTube trending
        youtube_trending = youtube_service.get_trending_music(region_code="ET", max_results=25)
        
        if not youtube_trending:
            return []
        
        # Search for matching internal songs
        matched_songs = []
        for video in youtube_trending[:limit]:
            if video.artist:
                # Try to find matching internal song
                matches = (
                    self.db.query(models.LibrarySong)
                    .filter(
                        or_(
                            models.LibrarySong.title.ilike(f"%{video.title.split(' - ')[-1][:30]}%"),
                            models.LibrarySong.artist.ilike(f"%{video.artist}%")
                        )
                    )
                    .limit(1)
                    .all()
                )
                if matches:
                    matched_songs.append(matches[0])
        
        return matched_songs
    
    def _get_random_candidates(
        self,
        exclude_user_id: int,
        limit: int
    ) -> List[models.LibrarySong]:
        """Get random songs for exploration."""
        return (
            self.db.query(models.LibrarySong)
            .filter(
                ~models.LibrarySong.id.in_(
                    self._get_user_song_ids(exclude_user_id)
                )
            )
            .order_by(func.random())
            .limit(limit)
            .all()
        )
    
    def _get_user_song_ids(self, user_id: int) -> List[int]:
        """Get song IDs user has recently played."""
        recent = self.repository.playback.get_user_recent_events(
            user_id, hours=168, limit=100
        )
        return list({e.song_id for e in recent})


# ============================================================================
# LAYER 2: RANKING ENGINE
# ============================================================================

class RankingEngine:
    """
    Layer 2: Score candidates using multiple signals.
    
    Scoring Formula:
    - Completion Rate: 45% weight
    - Skip Rate (inverse): 25% weight  
    - Play Frequency: 20% weight
    - Recency: 10% weight
    - YouTube Boost: +up to 20% (max)
    """
    
    def __init__(self, repository: RecommendationRepository, db: Session):
        self.repository = repository
        self.db = db
    
    def rank_candidates(
        self,
        user_id: int,
        candidates: List[models.LibrarySong],
        include_youtube_boost: bool = True,
        region: str = "ET"
    ) -> List[RankedSong]:
        """Rank all candidates using scoring algorithm."""
        if not candidates:
            return []
        
        # Get song statistics
        song_ids = [s.id for s in candidates]
        stats = self.repository.playback.get_song_event_stats(song_ids, hours=24 * 7)
        
        # Get YouTube boosts if enabled
        youtube_boosts = {}
        if include_youtube_boost and youtube_service.enabled:
            internal_songs = [
                {
                    "id": s.id,
                    "title": s.title,
                    "artist": s.artist,
                    "current_score": 50.0  # Default base
                }
                for s in candidates
            ]
            youtube_boosts = youtube_service.match_and_boost_internal_songs(
                internal_songs, region
            )
        
        # Score each candidate
        ranked: List[RankedSong] = []
        for song in candidates:
            song_stats = stats.get(song.id, {})
            base_score, reasons, breakdown = self._calculate_base_score(song, song_stats)
            
            # Apply YouTube boost (max 20%)
            youtube_boost = 0.0
            if song.id in youtube_boosts:
                boost_result = youtube_boosts[song.id]
                youtube_boost = min(boost_result.boost_score, 20.0)
                reasons.append(f"YouTube trending (+{youtube_boost:.1f})")
            
            final_score = base_score + youtube_boost
            
            ranked.append(RankedSong(
                song=song,
                base_score=round(base_score, 4),
                final_score=round(final_score, 4),
                reasons=reasons[:4],
                breakdown=breakdown,
                youtube_boost=round(youtube_boost, 2)
            ))
        
        # Sort by final score
        ranked.sort(key=lambda x: x.final_score, reverse=True)
        
        logger.info(f"Ranked {len(ranked)} candidates")
        return ranked
    
    def _calculate_base_score(
        self,
        song: models.LibrarySong,
        stats: Dict
    ) -> Tuple[float, List[str], schemas.RecommendationBreakdown]:
        """
        Calculate base score (80% of final).
        
        Returns: (score, reasons, breakdown)
        """
        completion_rate = float(stats.get("completion_rate", 0.0))
        skip_rate = float(stats.get("skip_rate", song.skip_rate or 0.3))
        play_count = float(stats.get("play_count", song.play_count_7d or 0))
        recency = self._calculate_recency_score(
            stats.get("last_played_at"),
            song.release_date
        )
        
        # Score components
        completion_score = completion_rate * 45.0
        skip_score = (1.0 - min(skip_rate, 1.0)) * 25.0
        popularity_score = min(play_count / 10.0, 20.0)
        recency_score = recency * 10.0
        
        total_score = completion_score + skip_score + popularity_score + recency_score
        
        # Build reasons
        reasons = []
        if completion_rate >= 0.6:
            reasons.append("High completion rate")
        if skip_rate <= 0.2:
            reasons.append("Low skip rate")
        if play_count >= 10:
            reasons.append("Trending")
        if song.genre:
            reasons.append(f"Genre: {song.genre}")
        
        breakdown = schemas.RecommendationBreakdown(
            completion_rate=round(completion_rate, 4),
            skip_rate=round(skip_rate, 4),
            popularity=round(popularity_score, 4),
            recency=round(recency_score, 4),
            diversity_adjustment=0.0,
            session_penalty=0.0,
        )
        
        return total_score, reasons, breakdown
    
    def _calculate_recency_score(
        self,
        last_played_at: Optional[datetime],
        release_date: Optional[str]
    ) -> float:
        """Calculate recency score (0-1)."""
        if last_played_at:
            if last_played_at.tzinfo is None:
                last_played_at = last_played_at.replace(tzinfo=UTC)
            age_hours = max((datetime.now(UTC) - last_played_at).total_seconds() / 3600, 0.0)
            return exp(-age_hours / 72.0)  # Decay over 3 days
        
        if release_date:
            try:
                released = datetime.strptime(release_date, "%Y-%m-%d").date()
                age_days = max((date.today() - released).days, 0)
                return exp(-age_days / 30.0)  # Decay over 30 days
            except ValueError:
                pass
        
        return 0.5  # Neutral for unknown


# ============================================================================
# LAYER 3: SESSION OPTIMIZATION
# ============================================================================

class SessionOptimizer:
    """
    Layer 3: Optimize session flow and reduce fatigue.
    
    Rules:
    - No repeats within last 10 songs
    - No same artist twice in a row
    - Diversity bonus for new genres/artists
    - Penalty for recently skipped songs
    """
    
    def __init__(self, repository: RecommendationRepository):
        self.repository = repository
    
    def optimize_session(
        self,
        user_id: int,
        ranked_songs: List[RankedSong],
        limit: int
    ) -> List[RankedSong]:
        """Apply session optimization rules."""
        # Get recent context
        recent_events = self.repository.playback.get_user_recent_events(
            user_id, hours=12, limit=25
        )
        recent_song_ids = {e.song_id for e in recent_events}
        recent_artists = [e.song.artist for e in recent_events if e.song and e.song.artist]
        recent_genres = [e.song.genre for e in recent_events if e.song and e.song.genre]
        
        # Get recently skipped songs
        skipped_songs = self.repository.playback.get_recently_skipped_songs(
            user_id, hours=24, limit=25
        )
        
        optimized: List[RankedSong] = []
        remaining = ranked_songs[:]
        
        while remaining and len(optimized) < limit:
            best_idx = 0
            best_adjusted_score = float("-inf")
            
            for idx, ranked in enumerate(remaining):
                adjusted_score, diversity_adj, penalty = self._calculate_session_score(
                    ranked,
                    recent_artists,
                    recent_genres,
                    skipped_songs,
                    {r.song.id for r in optimized}
                )
                
                if adjusted_score > best_adjusted_score:
                    best_adjusted_score = adjusted_score
                    best_idx = idx
                    # Update breakdown
                    remaining[idx].breakdown.diversity_adjustment = round(diversity_adj, 4)
                    remaining[idx].breakdown.session_penalty = round(penalty, 4)
                    remaining[idx].final_score = round(adjusted_score, 4)
            
            chosen = remaining.pop(best_idx)
            optimized.append(chosen)
            
            # Update context
            recent_artists.append(chosen.song.artist)
            recent_genres.append(chosen.song.genre)
        
        return optimized
    
    def _calculate_session_score(
        self,
        ranked: RankedSong,
        recent_artists: List[str],
        recent_genres: List[str],
        skipped_songs: Set[int],
        queued_ids: Set[int]
    ) -> Tuple[float, float, float]:
        """
        Calculate session-adjusted score.
        
        Returns: (adjusted_score, diversity_adjustment, session_penalty)
        """
        diversity_adj = 0.0
        penalty = 0.0
        
        # Skip penalty
        if ranked.song.id in skipped_songs:
            penalty -= 18.0
        
        # Repeat penalty
        if ranked.song.id in queued_ids:
            penalty -= 50.0
        
        # Artist diversity
        if recent_artists:
            if ranked.song.artist == recent_artists[-1]:
                penalty -= 10.0  # Same artist as last
            elif ranked.song.artist not in recent_artists[-3:]:
                diversity_adj += 4.0  # New artist bonus
        
        # Genre diversity
        if recent_genres:
            if ranked.song.genre != recent_genres[-1]:
                diversity_adj += 2.5  # Genre variety
            elif recent_genres.count(ranked.song.genre) >= 2:
                penalty -= 3.0  # Genre fatigue
        
        # If song was recently played (in last 10), big penalty
        if recent_artists and len(recent_artists) >= 10:
            recent_songs_artists = recent_artists[-10:]
            if ranked.song.artist in recent_songs_artists:
                penalty -= 8.0
        
        adjusted_score = ranked.final_score + diversity_adj + penalty
        return adjusted_score, diversity_adj, penalty


# ============================================================================
# LAYER 4: EXPLORATION VS EXPLOITATION
# ============================================================================

class ExplorationController:
    """
    Layer 4: Balance safe recommendations with exploration.
    
    Strategy:
    - 80% Exploitation (top-ranked songs)
    - 20% Exploration (random/diverse candidates)
    """
    
    def __init__(self, candidate_layer: CandidateGenerationLayer, db: Session):
        self.candidate_layer = candidate_layer
        self.db = db
        self.exploration_rate = 0.20  # 20%
    
    def apply_exploration(
        self,
        user_id: int,
        optimized_songs: List[RankedSong],
        candidate_pool: CandidatePool,
        limit: int
    ) -> List[RankedSong]:
        """
        Mix exploitation with exploration.
        
        Returns final recommendation list with 80/20 split.
        """
        if not optimized_songs:
            return []
        
        # Calculate split
        exploit_count = int(limit * (1 - self.exploration_rate))
        explore_count = limit - exploit_count
        
        # Get exploitation songs (already optimized)
        exploitation_songs = optimized_songs[:exploit_count]
        
        # Get exploration songs
        exploration_songs = self._get_exploration_songs(
            user_id,
            candidate_pool,
            exploitation_songs,
            explore_count
        )
        
        # Merge: interleave exploration every 5th position
        final_list: List[RankedSong] = []
        exp_idx = 0
        exp_total = len(exploration_songs)
        
        for i, song in enumerate(exploitation_songs):
            final_list.append(song)
            # Add exploration song every 4th position (after 4 exploitation)
            if (i + 1) % 4 == 0 and exp_idx < exp_total:
                final_list.append(exploration_songs[exp_idx])
                exp_idx += 1
        
        # Add any remaining exploration songs
        while exp_idx < exp_total and len(final_list) < limit:
            final_list.append(exploration_songs[exp_idx])
            exp_idx += 1
        
        # Trim to limit
        final_list = final_list[:limit]
        
        logger.info(
            f"Final mix for user {user_id}: "
            f"{len([s for s in final_list if s.source != 'exploration'])} exploitation, "
            f"{len([s for s in final_list if s.source == 'exploration'])} exploration"
        )
        
        return final_list
    
    def _get_exploration_songs(
        self,
        user_id: int,
        pool: CandidatePool,
        already_selected: List[RankedSong],
        count: int
    ) -> List[RankedSong]:
        """Get diverse exploration candidates."""
        selected_ids = {s.song.id for s in already_selected}
        
        # Combine random and YouTube candidates not already selected
        exploration_candidates = (
            pool.from_random + pool.from_youtube
        )
        
        # Filter out already selected
        exploration_candidates = [
            s for s in exploration_candidates if s.id not in selected_ids
        ]
        
        # Random shuffle for diversity
        random.shuffle(exploration_candidates)
        
        # Create RankedSong objects for exploration
        exploration_songs: List[RankedSong] = []
        for song in exploration_candidates[:count]:
            exploration_songs.append(RankedSong(
                song=song,
                base_score=40.0,  # Neutral score
                final_score=40.0,
                reasons=["Discovery"],
                breakdown=schemas.RecommendationBreakdown(
                    completion_rate=0.5,
                    skip_rate=0.3,
                    popularity=5.0,
                    recency=5.0,
                    diversity_adjustment=0.0,
                    session_penalty=0.0,
                ),
                source="exploration"
            ))
        
        return exploration_songs


# ============================================================================
# MAIN RECOMMENDATION SERVICE
# ============================================================================

class EnhancedRecommendationService:
    """
    Main service coordinating the 4-layer recommendation engine.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = RecommendationRepository(db)
        
        # Initialize layers
        self.candidate_layer = CandidateGenerationLayer(self.repository, db)
        self.ranking_engine = RankingEngine(self.repository, db)
        self.session_optimizer = SessionOptimizer(self.repository)
        self.exploration_controller = ExplorationController(self.candidate_layer, db)
        
        settings = get_settings()
        self.cache_ttl = getattr(settings, 'recommendation_cache_ttl_seconds', 1800)
    
    def get_next_recommendation(
        self,
        user_id: int,
        current_song_id: Optional[str] = None,
        location: Optional[str] = None
    ) -> schemas.RecommendationNextResponse:
        """
        Get the single best next song recommendation.
        """
        self._ensure_user_exists(user_id)
        
        # Check cache
        cache_key = f"rec:next:{user_id}:{current_song_id or 'none'}"
        cached = cache.get(cache_key)
        if cached:
            return schemas.RecommendationNextResponse.model_validate(cached)
        
        # Generate single recommendation
        candidates = self.candidate_layer.generate_candidates(
            user_id, current_song_id, location
        )
        
        # Flatten candidates
        all_candidates = list(set(
            candidates.from_history +
            candidates.from_genre +
            candidates.from_artist +
            candidates.from_trending
        ))
        
        if current_song_id:
            all_candidates = [c for c in all_candidates if c.navidrome_song_id != current_song_id]
        
        if not all_candidates:
            # Fallback to catalog
            all_candidates = self.repository.songs.list_catalog(limit=50)
        
        # Rank
        ranked = self.ranking_engine.rank_candidates(
            user_id, all_candidates, region=location or "ET"
        )
        
        if not ranked:
            raise ValueError("No recommendations available")
        
        # Get top recommendation with session optimization
        optimized = self.session_optimizer.optimize_session(user_id, ranked[:10], limit=1)
        
        if not optimized:
            raise ValueError("No recommendations available after optimization")
        
        top_song = optimized[0]
        
        response = schemas.RecommendationNextResponse(
            generated_at=datetime.now(UTC),
            current_song_id=current_song_id,
            recommendations=[self._serialize_ranked_song(top_song)]
        )
        
        # Cache for 5 minutes (short TTL for next song)
        cache.set(cache_key, response.model_dump(mode="json"), ttl=300)
        
        return response
    
    def get_personalized_feed(
        self,
        user_id: int,
        location: Optional[str] = None,
        limit: int = 12
    ) -> schemas.RecommendationHomeResponse:
        """
        Get personalized "For You" recommendation feed.
        """
        self._ensure_user_exists(user_id)
        
        # Check cache
        cache_key = f"rec:feed:{user_id}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return schemas.RecommendationHomeResponse.model_validate(cached)
        
        # Layer 1: Generate candidates
        candidate_pool = self.candidate_layer.generate_candidates(
            user_id, location=location
        )
        
        # Flatten and deduplicate
        all_candidates = list(set(
            candidate_pool.from_history +
            candidate_pool.from_genre +
            candidate_pool.from_artist +
            candidate_pool.from_trending
        ))
        
        if not all_candidates:
            all_candidates = self.repository.songs.list_catalog(limit=100)
        
        # Layer 2: Rank
        ranked = self.ranking_engine.rank_candidates(
            user_id, all_candidates, region=location or "ET"
        )
        
        # Layer 3: Optimize session
        optimized = self.session_optimizer.optimize_session(
            user_id, ranked, limit=limit
        )
        
        # Layer 4: Apply exploration (80/20 split)
        final_recommendations = self.exploration_controller.apply_exploration(
            user_id, optimized, candidate_pool, limit
        )
        
        response = schemas.RecommendationHomeResponse(
            generated_at=datetime.now(UTC),
            recommendations=[
                self._serialize_ranked_song(r) for r in final_recommendations
            ]
        )
        
        # Cache for 30 minutes
        cache.set(cache_key, response.model_dump(mode="json"), ttl=self.cache_ttl)
        
        return response
    
    def get_trending(
        self,
        location: Optional[str] = None,
        location_level: str = "global",
        limit: int = 12
    ) -> schemas.TrendingResponse:
        """
        Get trending songs based on internal playback activity.
        """
        cache_key = f"rec:trending:{location_level}:{location}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return schemas.TrendingResponse.model_validate(cached)
        
        # Get trending from internal system
        trending = self.repository.playback.calculate_trending_songs(
            location_level=location_level,
            location_value=location,
            hours=24,
            limit=limit * 2  # Get extra for filtering
        )
        
        if not trending:
            # Fallback to catalog
            songs = self.repository.songs.list_catalog(limit=limit)
        else:
            song_ids = [t[0] for t in trending]
            songs = (
                self.db.query(models.LibrarySong)
                .filter(models.LibrarySong.id.in_(song_ids))
                .all()
            )
            # Sort by trending order
            song_map = {s.id: s for s in songs}
            songs = [song_map[sid] for sid in song_ids if sid in song_map]
        
        # Get stats
        stats = self.repository.playback.get_song_event_stats(
            [s.id for s in songs], hours=24 * 7
        )
        
        response = schemas.TrendingResponse(
            generated_at=datetime.now(UTC),
            recommendations=[
                schemas.TrendingSongResponse(
                    song_id=s.navidrome_song_id,
                    title=s.title,
                    artist=s.artist,
                    genre=s.genre,
                    stream_url=s.stream_path,
                    play_count=int(stats.get(s.id, {}).get("play_count", s.play_count_7d)),
                    completion_rate=round(
                        float(stats.get(s.id, {}).get("completion_rate", 0.0)), 4
                    ),
                    skip_rate=round(
                        float(stats.get(s.id, {}).get("skip_rate", s.skip_rate)), 4
                    ),
                    hot_score=round(
                        self._calculate_hot_score(s, stats.get(s.id, {})), 4
                    ),
                    metadata={"source": "internal", "location": location or "global"}
                )
                for s in songs[:limit]
            ]
        )
        
        # Cache for 10 minutes
        cache.set(cache_key, response.model_dump(mode="json"), ttl=600)
        
        return response
    
    def get_top_songs(self, limit: int = 12) -> schemas.RecommendationHomeResponse:
        """
        Get top/popular songs (convenience method for API compatibility).
        Returns the highest-played songs from the catalog.
        """
        songs = self.repository.songs.list_catalog(limit=limit * 2)
        
        # Rank by play count
        ranked = []
        for song in songs[:limit]:
            ranked.append(RankedSong(
                song=song,
                base_score=float(song.play_count_7d or 0),
                final_score=float(song.play_count_7d or 0),
                reasons=["Popular"],
                breakdown=schemas.RecommendationBreakdown(
                    completion_rate=0.5,
                    skip_rate=song.skip_rate or 0.3,
                    popularity=float(song.play_count_7d or 0),
                    recency=0.5,
                    diversity_adjustment=0.0,
                    session_penalty=0.0,
                ),
                source="internal"
            ))
        
        ranked.sort(key=lambda x: x.final_score, reverse=True)
        
        return schemas.RecommendationHomeResponse(
            generated_at=datetime.now(UTC),
            recommendations=[self._serialize_ranked_song(r) for r in ranked[:limit]]
        )
    
    def get_trending_songs(self, location: Optional[str] = None, limit: int = 12) -> schemas.TrendingResponse:
        """Alias for get_trending - API compatibility method."""
        return self.get_trending(location=location, limit=limit)
    
    def get_friends_activity(self, user_id: int, limit: int = 12) -> schemas.RecommendationHomeResponse:
        """
        Get activity-based recommendations from peers.
        Returns songs that user's peers have recently played.
        """
        self._ensure_user_exists(user_id)
        
        cache_key = f"rec:friends:{user_id}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return schemas.RecommendationHomeResponse.model_validate(cached)
        
        # Get user's peers
        peers = self.repository.users.list_peers(user_id)
        if not peers:
            # Fallback to trending if no peers
            trending = self.get_trending(limit=limit)
            return schemas.RecommendationHomeResponse(
                generated_at=datetime.now(UTC),
                recommendations=[
                    schemas.RecommendationSong(
                        song_id=s.song_id,
                        title=s.title,
                        artist=s.artist,
                        genre=s.genre,
                        stream_url=s.stream_url,
                        score=s.hot_score,
                        reasons=["Trending"],
                        breakdown=schemas.RecommendationBreakdown(
                            completion_rate=s.completion_rate,
                            skip_rate=s.skip_rate,
                            popularity=float(s.play_count),
                            recency=0.8,
                            diversity_adjustment=0.0,
                            session_penalty=0.0,
                        ),
                        source="trending",
                        source_metadata={"hot_score": s.hot_score}
                    )
                    for s in trending.recommendations
                ]
            )
        
        # Get recent activity from peers
        peer_ids = [p.id for p in peers]
        recent_events = (
            self.db.query(models.PlaybackEvent)
            .filter(models.PlaybackEvent.user_id.in_(peer_ids))
            .filter(models.PlaybackEvent.event_type == "complete")
            .order_by(desc(models.PlaybackEvent.timestamp))
            .limit(50)
            .all()
        )
        
        # Extract unique songs
        song_ids = list({e.song_id for e in recent_events})[:limit]
        if not song_ids:
            trending = self.get_trending(limit=limit)
            return schemas.RecommendationHomeResponse(
                generated_at=datetime.now(UTC),
                recommendations=[
                    schemas.RecommendationSong(
                        song_id=s.song_id,
                        title=s.title,
                        artist=s.artist,
                        genre=s.genre,
                        stream_url=s.stream_url,
                        score=s.hot_score,
                        reasons=["Trending"],
                        breakdown=schemas.RecommendationBreakdown(
                            completion_rate=s.completion_rate,
                            skip_rate=s.skip_rate,
                            popularity=float(s.play_count),
                            recency=0.8,
                            diversity_adjustment=0.0,
                            session_penalty=0.0,
                        ),
                        source="trending",
                        source_metadata={"hot_score": s.hot_score}
                    )
                    for s in trending.recommendations
                ]
            )
        
        songs = (
            self.db.query(models.LibrarySong)
            .filter(models.LibrarySong.id.in_(song_ids))
            .all()
        )
        
        ranked = []
        for song in songs:
            ranked.append(RankedSong(
                song=song,
                base_score=50.0,
                final_score=50.0,
                reasons=["Friends are listening"],
                breakdown=schemas.RecommendationBreakdown(
                    completion_rate=0.6,
                    skip_rate=0.2,
                    popularity=float(song.play_count_7d or 0),
                    recency=0.7,
                    diversity_adjustment=5.0,
                    session_penalty=0.0,
                ),
                source="friends"
            ))
        
        response = schemas.RecommendationHomeResponse(
            generated_at=datetime.now(UTC),
            recommendations=[self._serialize_ranked_song(r) for r in ranked]
        )
        
        cache.set(cache_key, response.model_dump(mode="json"), ttl=300)
        return response
    
    def _ensure_user_exists(self, user_id: int):
        """Verify user exists."""
        user = self.repository.users.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
    
    def _serialize_ranked_song(self, ranked: RankedSong) -> schemas.RecommendationSong:
        """Convert RankedSong to API response schema."""
        return schemas.RecommendationSong(
            song_id=ranked.song.navidrome_song_id,
            title=ranked.song.title,
            artist=ranked.song.artist,
            genre=ranked.song.genre,
            stream_url=ranked.song.stream_path,
            score=ranked.final_score,
            reasons=ranked.reasons,
            breakdown=ranked.breakdown,
            source=ranked.source,
            source_metadata={
                "base_score": ranked.base_score,
                "youtube_boost": ranked.youtube_boost,
            } if ranked.youtube_boost > 0 else {}
        )
    
    def _calculate_hot_score(self, song: models.LibrarySong, stats: Dict) -> float:
        """Calculate hot/trending score."""
        completions = stats.get("complete_count", 0)
        plays = stats.get("play_count", song.play_count_7d or 0)
        skip_rate = stats.get("skip_rate", song.skip_rate or 0.3)
        
        return (
            completions * 3.0 +
            plays * 1.0 +
            (1.0 - min(skip_rate, 1.0)) * 10.0
        )
