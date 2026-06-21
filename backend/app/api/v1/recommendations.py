"""
Recommendations API - Home Feed Endpoints
Implements the complete home feed contract:
- /feed/top - Top songs in location
- /feed/trending - Trending songs
- /feed/for-you - Personalized feed
- /feed/friends - Friends listening
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app import models, schemas
from app.db import get_db
from app.schemas.recommendation import get_next_song
from app.core.security import get_current_user_id
from app.services.recommendation_engine import EnhancedRecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/next", response_model=schemas.RecommendationNextResponse)
def next_song(
    song_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get next song recommendation (legacy endpoint)"""
    song = get_next_song(db, user_id, song_id)

    if not song:
        raise HTTPException(status_code=404, detail="No recommendation found")

    return song


@router.get("/feed")
def get_recommendation_feed(
    user_id: int,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Compatibility feed endpoint used by the v1 client and tests."""
    songs = (
        db.query(models.LibrarySong)
        .order_by(models.LibrarySong.play_count_7d.desc(), models.LibrarySong.id.asc())
        .limit(limit)
        .all()
    )
    return {
        "user_id": user_id,
        "recommendations": [
            {
                "song_id": song.navidrome_song_id,
                "title": song.title,
                "artist": song.artist,
                "genre": song.genre,
                "source": "internal",
                "source_metadata": {
                    "play_count_7d": song.play_count_7d,
                    "like_count_7d": song.like_count_7d,
                },
            }
            for song in songs
        ],
    }


@router.get("/feed/top")
def get_top_feed(
    location: str = Query(..., description="User's location code (e.g., ET, US)"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get top songs in user's location.
    Returns the most popular songs in the specified location.
    """
    rec_service = EnhancedRecommendationService(db)
    top_songs = rec_service.get_top_songs(location, limit)
    
    return {
        "type": "top",
        "location": location,
        "songs": top_songs
    }


@router.get("/feed/trending")
def get_trending_feed(
    location: str = Query(..., description="User's location code"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get trending songs.
    Returns songs that are currently trending in the user's location.
    """
    rec_service = EnhancedRecommendationService(db)
    trending = rec_service.get_trending_songs(location, limit)
    
    return {
        "type": "trending",
        "location": location,
        "songs": trending
    }


@router.get("/feed/for-you")
def get_for_you_feed(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get personalized feed for the user.
    Returns a mix of recommendations based on user's listening history, preferences, and location.
    """
    rec_service = EnhancedRecommendationService(db)
    personalized = rec_service.get_personalized_feed(str(user_id), limit)
    
    return {
        "type": "for_you",
        "user_id": user_id,
        "songs": personalized
    }


@router.get("/feed/friends")
def get_friends_feed(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get songs that friends are currently listening to.
    Returns a feed of songs from the user's social circle.
    """
    rec_service = EnhancedRecommendationService(db)
    friends_songs = rec_service.get_friends_activity(str(user_id), limit)
    
    return {
        "type": "friends",
        "user_id": user_id,
        "songs": friends_songs
    }


@router.get("/analytics")
def get_recommendation_analytics(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get recommendation analytics for a user.
    Returns statistics about recommendation performance and user engagement.
    This is a placeholder - implement actual analytics tracking.
    """
    # TODO: Implement actual analytics tracking with recommendation_events table
    # For now, return placeholder data
    from app.repositories.playback_repository import PlaybackRepository
    repo = PlaybackRepository(db)
    
    recent_events = repo.get_user_recent_events(user_id, hours=24 * 7, limit=100, event_types=["play"])
    
    return {
        "user_id": user_id,
        "total_recommendations_shown": len(recent_events),
        "recommendation_click_rate": 0.45,  # Placeholder
        "average_session_length": 1800,  # Placeholder (30 minutes in seconds)
        "top_genres": ["Ethiopian Music", "Pop", "Traditional"],  # Placeholder
        "recommendation_sources": {
            "collaborative": 0.4,
            "content_based": 0.3,
            "trending": 0.2,
            "random": 0.1,
        },
    }


@router.get("/explain")
def explain_recommendation(
    user_id: int,
    song_id: str,
    db: Session = Depends(get_db),
):
    """
    Explain why a song was recommended to a user.
    Returns the factors and reasoning behind the recommendation.
    This is a placeholder - implement actual explainability logic.
    """
    # TODO: Implement actual explainability based on recommendation factors
    # For now, return placeholder explanation
    from app.models.song import LibrarySong
    
    song = db.query(LibrarySong).filter(
        LibrarySong.navidrome_song_id == song_id
    ).first()
    
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    return {
        "user_id": user_id,
        "song_id": song_id,
        "song_title": song.title,
        "artist": song.artist,
        "recommendation_reasons": [
            {
                "factor": "genre_match",
                "confidence": 0.85,
                "description": f"You enjoy {song.genre} music",
            },
            {
                "factor": "artist_similarity",
                "confidence": 0.72,
                "description": "Similar to artists you've listened to",
            },
            {
                "factor": "popularity",
                "confidence": 0.65,
                "description": "Trending in your region",
            },
        ],
        "overall_confidence": 0.74,
    }

