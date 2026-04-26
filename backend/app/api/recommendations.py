"""
Recommendation API endpoints.

Endpoints:
- GET /recommendations/next - Get single next best song
- GET /recommendations/for-you - Get personalized feed
- GET /recommendations/trending - Get trending songs
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
import logging

from app import schemas
from app.db.session import get_db
from app.services.recommendation_engine import EnhancedRecommendationService
from app.core.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommendation_service(db: Session = Depends(get_db)) -> EnhancedRecommendationService:
    """Dependency to get recommendation service."""
    return EnhancedRecommendationService(db)


@router.get(
    "/next",
    response_model=schemas.RecommendationNextResponse,
    summary="Get next best song recommendation",
    description="Returns the single best song to play next based on current context."
)
async def get_next_recommendation(
    request: Request,
    user_id: int = Query(..., description="User ID requesting recommendation"),
    current_song_id: Optional[str] = Query(
        None,
        description="Current song ID (if any) for context-aware recommendations"
    ),
    location: Optional[str] = Query(
        None,
        description="User location for regional trending (e.g., 'Addis Ababa', 'ET')"
    ),
    service: EnhancedRecommendationService = Depends(get_recommendation_service)
):
    """
    Get the next best song recommendation.
    
    This endpoint uses the 4-layer recommendation engine:
    1. Candidate generation from user history, trending, and YouTube
    2. Ranking with completion/skip/popularity scores
    3. Session optimization to avoid repeats and fatigue
    4. No exploration (always best choice for next song)
    
    YouTube integration provides up to 20% boost for trending songs.
    """
    try:
        logger.info(
            f"Next recommendation request: user={user_id}, "
            f"current={current_song_id}, location={location}"
        )
        
        response = service.get_next_recommendation(
            user_id=user_id,
            current_song_id=current_song_id,
            location=location
        )
        
        # Log for analytics
        logger.info(
            f"Next recommendation: user={user_id}, "
            f"song={response.recommendations[0].song_id if response.recommendations else 'none'}, "
            f"score={response.recommendations[0].score if response.recommendations else 0:.2f}"
        )
        
        return response
        
    except ValueError as e:
        logger.warning(f"Recommendation error for user {user_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in next recommendation: {e}")
        raise HTTPException(status_code=500, detail="Recommendation service error")


@router.get(
    "/for-you",
    response_model=schemas.RecommendationHomeResponse,
    summary="Get personalized recommendation feed",
    description="Returns a personalized list of recommended songs with 80/20 exploitation/exploration mix."
)
async def get_personalized_feed(
    request: Request,
    user_id: int = Query(..., description="User ID for personalization"),
    limit: int = Query(
        12,
        ge=1,
        le=50,
        description="Number of recommendations to return"
    ),
    location: Optional[str] = Query(
        None,
        description="User location for regional trending"
    ),
    service: EnhancedRecommendationService = Depends(get_recommendation_service)
):
    """
    Get personalized "For You" recommendation feed.
    
    Returns a mix of:
    - 80% Exploitation: High-confidence recommendations based on your history
    - 20% Exploration: Diverse discovery songs to find new favorites
    
    Sources include:
    - Your listening history
    - Same genre/artist songs
    - Internal trending
    - YouTube trending (20% signal boost)
    - Random exploration
    
    Cached for 30 minutes per user.
    """
    try:
        logger.info(
            f"Personalized feed request: user={user_id}, limit={limit}, location={location}"
        )
        
        response = service.get_personalized_feed(
            user_id=user_id,
            location=location,
            limit=limit
        )
        
        logger.info(
            f"Personalized feed: user={user_id}, "
            f"returned={len(response.recommendations)} recommendations"
        )
        
        return response
        
    except ValueError as e:
        logger.warning(f"Feed error for user {user_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in personalized feed: {e}")
        raise HTTPException(status_code=500, detail="Recommendation service error")


@router.get(
    "/trending",
    response_model=schemas.TrendingResponse,
    summary="Get trending songs",
    description="Returns trending songs based on internal playback activity."
)
async def get_trending(
    request: Request,
    location: Optional[str] = Query(
        None,
        description="Filter by location (e.g., 'Addis Ababa', 'ET', 'global')"
    ),
    location_level: str = Query(
        "global",
        enum=["global", "country", "city"],
        description="Level of trending aggregation"
    ),
    limit: int = Query(
        12,
        ge=1,
        le=50,
        description="Number of trending songs to return"
    ),
    service: EnhancedRecommendationService = Depends(get_recommendation_service)
):
    """
    Get trending songs based on internal playback activity.
    
    Trending is calculated from:
    - Play counts (last 24 hours)
    - Completion rates
    - Skip rates (negative signal)
    
    Hot Score Formula:
    hot_score = (completions * 3) + (plays * 1) + ((1 - skip_rate) * 10)
    
    Supports location filtering:
    - Global: All users
    - Country: Filter by country code (e.g., 'ET')
    - City: Filter by city name
    
    YouTube trending is NOT included here - use /for-you for YouTube-boosted recommendations.
    
    Cached for 10 minutes.
    """
    try:
        logger.info(
            f"Trending request: location={location}, level={location_level}, limit={limit}"
        )
        
        response = service.get_trending(
            location=location,
            location_level=location_level,
            limit=limit
        )
        
        logger.info(f"Trending: returned={len(response.recommendations)} songs")
        
        return response
        
    except Exception as e:
        logger.error(f"Trending error: {e}")
        raise HTTPException(status_code=500, detail="Trending service error")


@router.post(
    "/feedback",
    summary="Record recommendation feedback",
    description="Record user feedback on a recommendation for model improvement."
)
async def record_recommendation_feedback(
    request: Request,
    user_id: int = Query(..., description="User ID"),
    song_id: str = Query(..., description="Song ID that was recommended"),
    action: str = Query(
        ...,
        enum=["played", "skipped", "completed", "liked", "disliked"],
        description="User action on the recommendation"
    ),
    db: Session = Depends(get_db)
):
    """
    Record user feedback on recommendations.
    
    This helps improve future recommendations by:
    - Tracking which recommendations were played
    - Learning skip patterns
    - Building user preference models
    
    Also invalidates recommendation caches to update quickly.
    """
    try:
        from app.repositories.playback_repo import PlaybackRepository
        
        playback_repo = PlaybackRepository(db)
        
        # Map action to event type
        event_type_map = {
            "played": "play",
            "skipped": "skip",
            "completed": "complete",
            "liked": "complete",  # Treat like as complete
            "disliked": "skip"    # Treat dislike as skip
        }
        
        event_type = event_type_map.get(action, "play")
        
        # Get song ID from navidrome_song_id
        from app.models.song import LibrarySong
        song = db.query(LibrarySong).filter(
            LibrarySong.navidrome_song_id == song_id
        ).first()
        
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        # Record the event
        playback_repo.record_event(
            user_id=user_id,
            song_id=song.id,
            event_type=event_type
        )
        
        # Invalidate user's recommendation cache
        cache.delete(f"rec:feed:{user_id}:*")
        cache.delete(f"rec:next:{user_id}:*")
        
        logger.info(
            f"Feedback recorded: user={user_id}, song={song_id}, action={action}"
        )
        
        return {"status": "recorded", "user_id": user_id, "song_id": song_id, "action": action}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback recording error: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.get(
    "/stats",
    summary="Get recommendation system statistics",
    description="Returns statistics about the recommendation system performance."
)
async def get_recommendation_stats(
    request: Request
):
    """
    Get recommendation system statistics and health.
    
    Returns:
    - YouTube integration status
    - Cache hit rates
    - Recent recommendation counts
    """
    try:
        from app.services.youtube_integration import youtube_service
        
        youtube_status = {
            "enabled": youtube_service.enabled,
            "weight": youtube_service.boost_weight if youtube_service.enabled else 0,
            "max_boost": youtube_service.max_boost_points if youtube_service.enabled else 0
        }
        
        return {
            "youtube_integration": youtube_status,
            "architecture": "4-layer (Candidates -> Ranking -> Session -> Exploration)",
            "exploration_rate": "20%",
            "caching": "Enabled (Redis/Memory fallback)",
            "endpoints": [
                "/recommendations/next",
                "/recommendations/for-you",
                "/recommendations/trending"
            ]
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")
