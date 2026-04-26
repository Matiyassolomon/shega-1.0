"""
Playback API with payment and access control
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/play", tags=["Playback"])


@router.post("/start")
async def start_playback(
    request: Request,
    device_id: str,
    current_song_id: Optional[str] = None,
    network_type: str = Header(default="wifi"),
    network_quality: float = Header(default=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start playback with payment and access control
    
    Flow:
    1. Authenticate & validate device
    2. Get next song from recommendation service
    3. CHECK ACCESS (free? purchased? subscription?)
    4. If no access -> return PAYMENT_REQUIRED with preview
    5. Check concurrent stream limits
    6. Determine audio quality
    7. Create playback session
    8. Generate Navidrome stream URL
    9. Return playback info
    """
    
    # 1. Validate device ownership
    from app.services.device_service import DeviceService
    device_service = DeviceService(db)
    device = device_service.validate_device(current_user.id, device_id)
    if not device:
        raise HTTPException(403, "Invalid or unauthorized device")
    
    # 2. Get next song recommendation
    from app.services.recommendation_engine import EnhancedRecommendationService
    
    rec_service = EnhancedRecommendationService(db)
    recommendation = rec_service.get_next_recommendation(
        user_id=current_user.id,
        current_song_id=current_song_id
    )
    
    if not recommendation or not recommendation.get("recommendations"):
        raise HTTPException(404, "No song available for playback")
    
    song_data = recommendation["recommendations"][0]
    song_id = song_data["song_id"]
    
    # 3. CHECK ACCESS CONTROL (KEY PAYMENT LOGIC)
    from app.services.access_control_service import AccessControlService
    
    access_service = AccessControlService(db)
    can_play, error_code, access_details = await access_service.check_playback_access(
        current_user.id, song_id
    )
    
    # 4. If no access, return PAYMENT_REQUIRED
    if not can_play:
        if error_code == "PAYMENT_REQUIRED":
            # Generate preview URL
            from app.services.navidrome_service import NavidromeService
            navidrome = NavidromeService()
            preview_url = navidrome.generate_preview_url(song_id, duration_seconds=30)
            
            return {
                "status": "PAYMENT_REQUIRED",
                "message": "Purchase required to play full song",
                "song_preview": {
                    "id": song_id,
                    "title": song_data.get("title", "Unknown"),
                    "artist": song_data.get("artist", "Unknown"),
                    "preview_url": preview_url,
                    "preview_duration": 30
                },
                "purchase_options": {
                    "individual": {
                        "price": access_details["price"],
                        "currency": access_details["currency"],
                        "purchase_url": f"/api/v1/payments/song-purchase?user_id={current_user.id}&song_id={song_id}"
                    },
                    "subscription": {
                        "available": access_details.get("requires_premium", False),
                        "tiers": ["premium", "premium_plus"],
                        "unlocks_all": True,
                        "upgrade_url": "/api/v1/payments/subscription"
                    }
                }
            }
        
        raise HTTPException(403, error_code or "Access denied")
    
    # 5. Check concurrent stream limits
    from app.services.playback_session_service import PlaybackSessionService
    
    session_service = PlaybackSessionService(db)
    stream_check = session_service.validate_stream_start(
        current_user.id, device.id
    )
    
    if not stream_check["allowed"]:
        # Option: terminate oldest session or reject
        if stream_check.get("can_terminate_oldest"):
            session_service.terminate_oldest_session(current_user.id)
            # Retry
            stream_check = session_service.validate_stream_start(
                current_user.id, device.id
            )
        
        if not stream_check["allowed"]:
            raise HTTPException(429, {
                "error": "CONCURRENT_LIMIT",
                "message": stream_check["reason"],
                "max_streams": stream_check["max_streams"],
                "active_sessions": stream_check["active_count"]
            })
    
    # 6. Determine audio quality
    from app.services.audio_quality_service import AudioQualityService
    
    audio_service = AudioQualityService()
    quality = audio_service.determine_quality(
        user=current_user,
        device=device,
        network_type=network_type,
        network_quality_score=network_quality
    )
    
    # 7. Create playback session
    session = session_service.create_session(
        user_id=current_user.id,
        device_id=device.id,
        song_id=song_id,
        audio_quality=quality.quality,
        bitrate=quality.bitrate_kbps
    )
    
    # 8. Generate Navidrome stream URL
    from app.services.navidrome_service import NavidromeService
    
    navidrome = NavidromeService()
    stream_url = navidrome.generate_stream_url(
        song_id=song_id,
        username=current_user.email or current_user.id,
        max_bitrate=quality.bitrate_kbps
    )
    
    # 9. Return complete playback info
    return {
        "status": "PLAYING",
        "song": {
            "id": song_id,
            "title": song_data.get("title", "Unknown"),
            "artist": song_data.get("artist", "Unknown"),
            "album": song_data.get("album"),
            "duration": song_data.get("duration", 0),
            "album_art": song_data.get("album_art_url")
        },
        "stream": {
            "url": stream_url,
            "quality": quality.quality,
            "bitrate": quality.bitrate_kbps,
            "codec": quality.codec,
            "quality_reason": quality.reason,
            "can_upgrade": quality.can_upgrade
        },
        "session": {
            "id": session.id,
            "started_at": session.started_at.isoformat() if hasattr(session, "started_at") else datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=4)).isoformat()
        },
        "access": {
            "type": access_details.get("access_type", "unknown"),
            "is_owned": access_details.get("access_type") == "purchase"
        },
        "limits": {
            "max_concurrent_streams": stream_check["max_streams"],
            "current_active_streams": stream_check["active_count"],
            "remaining_streams": stream_check["max_streams"] - stream_check["active_count"]
        },
        "recommendation_hint": recommendation.get("next_recommendation_hint")
    }


@router.get("/preview")
async def get_preview(
    song_id: str,
    duration: int = 30
):
    """Get 30-second preview for unpaid songs"""
    from app.services.navidrome_service import NavidromeService
    
    navidrome = NavidromeService()
    preview_url = navidrome.generate_preview_url(song_id, duration)
    
    return {
        "preview_url": preview_url,
        "duration": duration,
        "full_version_available": True
    }


@router.post("/heartbeat")
async def playback_heartbeat(
    session_id: str,
    position_ms: int,
    db: Session = Depends(get_db)
):
    """Keep playback session alive"""
    from app.services.playback_session_service import PlaybackSessionService
    
    session_service = PlaybackSessionService(db)
    updated = session_service.update_heartbeat(session_id, position_ms)
    
    if not updated:
        raise HTTPException(404, "Session not found or expired")
    
    return {"ok": True, "session_active": True}


@router.post("/stop")
async def stop_playback(
    session_id: str,
    db: Session = Depends(get_db)
):
    """End playback session"""
    from app.services.playback_session_service import PlaybackSessionService
    
    session_service = PlaybackSessionService(db)
    session_service.end_session(session_id)
    
    return {"stopped": True, "session_id": session_id}
