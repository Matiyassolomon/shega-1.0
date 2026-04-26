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
from app import schemas
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
