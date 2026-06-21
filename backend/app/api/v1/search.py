"""
Search API - Production search with autocomplete, ranking, and typo tolerance
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List
from app.models.song import LibrarySong
from app.db import get_db
from app.core.security import get_current_user_id
import re

router = APIRouter(prefix="/search", tags=["search"])


def fuzzy_match(query: str, text: str) -> float:
    """
    Calculate fuzzy match score between query and text.
    Returns a score between 0 and 1, where 1 is exact match.
    """
    if not query or not text:
        return 0.0
    
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Exact match
    if query_lower == text_lower:
        return 1.0
    
    # Contains match
    if query_lower in text_lower:
        return 0.8
    
    # Typo tolerance using simple character overlap
    query_chars = set(query_lower)
    text_chars = set(text_lower)
    overlap = len(query_chars & text_chars)
    if overlap > 0:
        return overlap / len(query_chars) * 0.5
    
    return 0.0


def calculate_relevance_score(song: LibrarySong, query: str) -> float:
    """
    Calculate relevance score for a song based on multiple factors.
    """
    title_score = fuzzy_match(query, song.title) * 1.0
    artist_score = fuzzy_match(query, song.artist) * 0.8
    genre_score = fuzzy_match(query, song.genre) * 0.5
    
    # Boost by popularity
    popularity_boost = min(song.play_count_7d / 1000, 0.3)
    
    # Boost by likes
    like_boost = min(song.like_count_7d / 100, 0.2)
    
    total_score = title_score + artist_score + genre_score + popularity_boost + like_boost
    return min(total_score, 1.0)


@router.get("/autocomplete")
def search_autocomplete(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Get autocomplete suggestions for search query.
    Returns song titles, artists, and genres matching the query.
    """
    if len(query) < 2:
        return {"suggestions": []}
    
    # Search for matching songs
    songs = db.query(LibrarySong).filter(
        or_(
            LibrarySong.title.ilike(f"%{query}%"),
            LibrarySong.artist.ilike(f"%{query}%"),
            LibrarySong.genre.ilike(f"%{query}%"),
        )
    ).limit(limit * 3).all()
    
    # Calculate relevance and sort
    scored_songs = []
    for song in songs:
        score = calculate_relevance_score(song, query)
        if score > 0.3:  # Minimum relevance threshold
            scored_songs.append((song, score))
    
    scored_songs.sort(key=lambda x: x[1], reverse=True)
    
    # Extract unique suggestions
    suggestions = []
    seen = set()
    
    for song, score in scored_songs[:limit]:
        # Add title suggestion
        if song.title.lower() not in seen:
            suggestions.append({
                "type": "song",
                "text": song.title,
                "artist": song.artist,
                "relevance": score,
            })
            seen.add(song.title.lower())
        
        # Add artist suggestion
        if song.artist.lower() not in seen:
            suggestions.append({
                "type": "artist",
                "text": song.artist,
                "relevance": score * 0.8,
            })
            seen.add(song.artist.lower())
        
        if len(suggestions) >= limit:
            break
    
    return {"suggestions": suggestions}


@router.get("/songs")
def search_songs(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = Query("relevance", regex="^(relevance|popularity|recent)$"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Search for songs with ranking and typo tolerance.
    Returns paginated results sorted by relevance, popularity, or recency.
    """
    # Base query with fuzzy matching
    songs = db.query(LibrarySong).filter(
        or_(
            LibrarySong.title.ilike(f"%{query}%"),
            LibrarySong.artist.ilike(f"%{query}%"),
            LibrarySong.genre.ilike(f"%{query}%"),
        )
    ).all()
    
    # Calculate relevance scores
    scored_songs = []
    for song in songs:
        score = calculate_relevance_score(song, query)
        if score > 0.2:  # Minimum relevance threshold
            scored_songs.append((song, score))
    
    # Sort based on preference
    if sort_by == "relevance":
        scored_songs.sort(key=lambda x: x[1], reverse=True)
    elif sort_by == "popularity":
        scored_songs.sort(key=lambda x: x[0].play_count_7d, reverse=True)
    elif sort_by == "recent":
        scored_songs.sort(key=lambda x: x[0].id, reverse=True)
    
    # Paginate
    total = len(scored_songs)
    paginated_songs = scored_songs[offset:offset + limit]
    
    return {
        "query": query,
        "total": total,
        "offset": offset,
        "limit": limit,
        "sort_by": sort_by,
        "results": [
            {
                "song_id": song.navidrome_song_id,
                "title": song.title,
                "artist": song.artist,
                "genre": song.genre,
                "play_count_7d": song.play_count_7d,
                "like_count_7d": song.like_count_7d,
                "cover_art_path": song.cover_art_path,
                "relevance_score": score,
            }
            for song, score in paginated_songs
        ],
    }


@router.get("/artists")
def search_artists(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Search for artists with typo tolerance.
    Returns unique artists matching the query.
    """
    # Get all songs by matching artists
    songs = db.query(LibrarySong).filter(
        LibrarySong.artist.ilike(f"%{query}%")
    ).all()
    
    # Group by artist and calculate scores
    artist_scores = {}
    for song in songs:
        if song.artist not in artist_scores:
            artist_scores[song.artist] = {
                "score": fuzzy_match(query, song.artist),
                "song_count": 0,
                "total_plays": 0,
            }
        artist_scores[song.artist]["song_count"] += 1
        artist_scores[song.artist]["total_plays"] += song.play_count_7d
    
    # Sort by relevance and popularity
    sorted_artists = sorted(
        artist_scores.items(),
        key=lambda x: (x[1]["score"], x[1]["total_plays"]),
        reverse=True,
    )
    
    return {
        "query": query,
        "results": [
            {
                "artist": artist,
                "song_count": data["song_count"],
                "total_plays": data["total_plays"],
                "relevance_score": data["score"],
            }
            for artist, data in sorted_artists[:limit]
        ],
    }
