from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel

from app import schemas
from app.db import get_db
from app.services import crud
from app.repositories.playback_repository import PlaybackRepository

router = APIRouter(prefix="/users", tags=["users"])


class PayoutRequestCreate(BaseModel):
    amount: float
    bank_account: str
    bank_name: str


@router.get("/{user_id}", response_model=schemas.UserProfileResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        return crud.get_user_profile(db, user_id)
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail="User not found") from exc
        raise


@router.get("/{user_id}/recently-played")
def get_recently_played(
    user_id: int,
    hours: int = 24,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Get recently played songs for a user.
    Returns songs with their last played timestamp and play count.
    """
    repo = PlaybackRepository(db)
    events = repo.get_user_recent_events(
        user_id=user_id,
        hours=hours,
        limit=limit,
        event_types=["play", "complete"]
    )
    
    # Group by song and get latest timestamp
    from collections import defaultdict
    song_data = defaultdict(lambda: {"last_played": None, "play_count": 0})
    
    for event in events:
        if event.song:
            song_data[event.song_id]["last_played"] = max(
                song_data[event.song_id]["last_played"] or event.timestamp,
                event.timestamp
            )
            song_data[event.song_id]["play_count"] += 1
            song_data[event.song_id]["song"] = event.song
    
    # Convert to list and sort by last played
    result = []
    for song_id, data in song_data.items():
        if data["song"]:
            result.append({
                "song_id": song_id,
                "title": data["song"].title,
                "artist": data["song"].artist,
                "album": data["song"].album,
                "genre": data["song"].genre,
                "cover_art": data["song"].cover_art,
                "last_played": data["last_played"].isoformat() if data["last_played"] else None,
                "play_count": data["play_count"],
            })
    
    result.sort(key=lambda x: x["last_played"] or "", reverse=True)
    return result[:limit]


@router.get("/{user_id}/liked-songs")
def get_liked_songs(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Get liked songs for a user.
    This is a placeholder - implement actual likes tracking in the database.
    """
    # TODO: Implement actual likes tracking with a user_likes table
    # For now, return empty list
    return []


@router.get("/artists/{artist_name}")
def get_artist_profile(
    artist_name: str,
    db: Session = Depends(get_db),
):
    """
    Get artist profile by aggregating songs by artist name.
    Returns artist info, top songs, albums, and statistics.
    """
    from app.models.song import LibrarySong
    
    # Get all songs by this artist
    songs = db.query(LibrarySong).filter(
        LibrarySong.artist == artist_name
    ).all()
    
    if not songs:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    # Aggregate statistics
    total_plays = sum(song.play_count_7d for song in songs)
    total_likes = sum(song.like_count_7d for song in songs)
    genres = list(set(song.genre for song in songs if song.genre))
    
    # Get top songs (by play count)
    top_songs = sorted(songs, key=lambda x: x.play_count_7d, reverse=True)[:10]
    
    # Get unique albums (from playlist_id or title grouping)
    albums = {}
    for song in songs:
        # Use playlist_id as album identifier if available, otherwise group by title prefix
        album_key = song.playlist_id or song.title.split('-')[0].strip() if '-' in song.title else 'Singles'
        if album_key not in albums:
            albums[album_key] = {
                'name': album_key,
                'song_count': 0,
                'cover_art': song.cover_art_path,
            }
        albums[album_key]['song_count'] += 1
    
    return {
        'artist_name': artist_name,
        'total_songs': len(songs),
        'total_plays': total_plays,
        'total_likes': total_likes,
        'genres': genres,
        'top_songs': [
            {
                'song_id': song.id,
                'title': song.title,
                'artist': song.artist,
                'genre': song.genre,
                'play_count': song.play_count_7d,
                'like_count': song.like_count_7d,
                'cover_art': song.cover_art_path,
            }
            for song in top_songs
        ],
        'albums': list(albums.values()),
    }


@router.get("/{user_id}/artist-dashboard")
def get_artist_dashboard(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get artist dashboard data including earnings, plays, and sales.
    This is a placeholder - implement actual artist earnings tracking.
    """
    # TODO: Implement actual artist earnings tracking with proper tables
    # For now, return placeholder data
    from app.models.song import LibrarySong
    
    # Get songs by this user (assuming user_id maps to artist)
    songs = db.query(LibrarySong).filter(
        LibrarySong.artist == f"Artist {user_id}"
    ).all()
    
    total_plays = sum(song.play_count_7d for song in songs)
    total_likes = sum(song.like_count_7d for song in songs)
    
    # Placeholder earnings calculation (0.01 ETB per play)
    earnings = total_plays * 0.01
    
    return {
        'total_earnings': earnings,
        'total_plays': total_plays,
        'total_likes': total_likes,
        'total_songs': len(songs),
        'recent_plays': total_plays // 7,  # Placeholder
        'recent_earnings': earnings / 7,  # Placeholder
    }


@router.get("/{user_id}/wallet")
def get_wallet(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get wallet balance and transaction history.
    This is a placeholder - implement actual wallet tracking.
    """
    # TODO: Implement actual wallet tracking with wallet_balance and wallet_transactions tables
    # For now, return placeholder data
    return {
        'balance': 0.0,
        'currency': 'ETB',
        'transactions': [],
    }


@router.post("/{user_id}/payout-requests")
def create_payout_request(
    user_id: int,
    request: PayoutRequestCreate,
    db: Session = Depends(get_db),
):
    """
    Create a payout request.
    This is a placeholder - implement actual payout request tracking.
    """
    # TODO: Implement actual payout request tracking with payout_requests table
    # For now, return placeholder response
    return {
        'id': f'payout-{user_id}-{int(request.amount)}',
        'user_id': user_id,
        'amount': request.amount,
        'bank_account': request.bank_account,
        'bank_name': request.bank_name,
        'status': 'pending',
        'created_at': '2024-01-01T00:00:00Z',
    }


@router.get("/{user_id}/payout-requests")
def get_payout_requests(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get payout requests for a user.
    This is a placeholder - implement actual payout request tracking.
    """
    # TODO: Implement actual payout request tracking with payout_requests table
    # For now, return empty list
    return []


@router.post("/{user_id}/ad-events")
def track_ad_event(
    user_id: int,
    event_type: str,
    ad_id: str,
    song_id: str,
    duration: float = 0,
    db: Session = Depends(get_db),
):
    """
    Track ad events (play, complete, skip) for revenue sharing.
    This is a placeholder - implement actual ad tracking with ad_events table.
    """
    # TODO: Implement actual ad tracking with ad_events table
    # For now, return placeholder response
    return {
        'id': f'ad-event-{user_id}-{ad_id}',
        'user_id': user_id,
        'event_type': event_type,
        'ad_id': ad_id,
        'song_id': song_id,
        'duration': duration,
        'timestamp': '2024-01-01T00:00:00Z',
    }


@router.get("/{user_id}/ad-revenue")
def get_ad_revenue(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get ad revenue statistics for an artist.
    This is a placeholder - implement actual ad revenue calculation.
    """
    # TODO: Implement actual ad revenue calculation from ad_events table
    # For now, return placeholder data
    return {
        'total_revenue': 0.0,
        'total_impressions': 0,
        'total_completions': 0,
        'revenue_per_impression': 0.01,
        'recent_revenue': 0.0,
    }


@router.get("/admin/dashboard")
def get_admin_dashboard(
    db: Session = Depends(get_db),
):
    """
    Get admin dashboard statistics.
    Returns overall platform metrics for admin monitoring.
    This is a placeholder - implement actual admin analytics.
    """
    # TODO: Implement actual admin analytics from various tables
    # For now, return placeholder data
    from app.models.song import LibrarySong
    
    total_songs = db.query(LibrarySong).count()
    total_plays = db.query(LibrarySong).with_entities(
        func.sum(LibrarySong.play_count_7d)
    ).scalar() or 0
    total_likes = db.query(LibrarySong).with_entities(
        func.sum(LibrarySong.like_count_7d)
    ).scalar() or 0
    
    return {
        'total_users': 1000,  # Placeholder
        'total_artists': 50,  # Placeholder
        'total_songs': total_songs,
        'total_plays': total_plays,
        'total_likes': total_likes,
        'total_revenue': 50000.0,  # Placeholder
        'active_subscriptions': 200,  # Placeholder
        'pending_payouts': 10,  # Placeholder
        'recent_signups': 25,  # Placeholder (last 7 days)
    }


@router.get("/admin/users")
def get_admin_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get list of users for admin management.
    This is a placeholder - implement actual user listing.
    """
    # TODO: Implement actual user listing from users table
    # For now, return placeholder data
    return {
        'total': 1000,
        'offset': offset,
        'limit': limit,
        'users': [
            {
                'id': i,
                'username': f'user{i}',
                'email': f'user{i}@example.com',
                'created_at': '2024-01-01T00:00:00Z',
                'is_active': True,
                'subscription_status': 'premium' if i % 3 == 0 else 'free',
            }
            for i in range(offset + 1, min(offset + limit + 1, 1001))
        ],
    }


@router.get("/admin/artists")
def get_admin_artists(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get list of artists for admin management.
    This is a placeholder - implement actual artist listing.
    """
    # TODO: Implement actual artist listing from songs table
    # For now, return placeholder data
    from app.models.song import LibrarySong
    
    artists = db.query(LibrarySong.artist).distinct().limit(limit * 2).all()
    
    return {
        'total': len(artists),
        'offset': offset,
        'limit': limit,
        'artists': [
            {
                'id': i,
                'name': artist[0],
                'song_count': 10 + (i % 20),
                'total_plays': 1000 + (i * 100),
                'total_revenue': 100.0 + (i * 10),
                'verified': i % 5 == 0,
            }
            for i, artist in enumerate(artists[offset:offset + limit])
        ],
    }


@router.get("/admin/payments")
def get_admin_payments(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get list of payments for admin management.
    This is a placeholder - implement actual payment listing.
    """
    # TODO: Implement actual payment listing from payments table
    # For now, return placeholder data
    return {
        'total': 500,
        'offset': offset,
        'limit': limit,
        'payments': [
            {
                'id': f'payment-{i}',
                'user_id': (i % 100) + 1,
                'amount': 199.0 if i % 2 == 0 else 25.0,
                'currency': 'ETB',
                'status': status or ('completed' if i % 3 == 0 else 'pending'),
                'payment_type': 'subscription' if i % 2 == 0 else 'song_purchase',
                'created_at': '2024-01-01T00:00:00Z',
            }
            for i in range(offset + 1, min(offset + limit + 1, 501))
        ],
    }


