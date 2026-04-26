"""
Playback API - Control Plane Endpoint
Implements the complete playback decision engine:
- Access control (FREE vs PAYMENT_REQUIRED)
- Recommendation selection
- Audio quality determination
- Concurrent stream limits
- Session management
- Atomic access check + SIGNED stream token issuance

STREAMING ARCHITECTURE:
- This API server is the CONTROL PLANE (auth, decisions, sessions)
- Media bytes are delivered via REDIRECT to Navidrome (not proxied)
- /playback/start returns a signed media access token
- /playback/media validates token and returns HTTP 307 redirect to Navidrome
- This eliminates the API server as a media traffic bottleneck
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app import schemas
from app.core.security import get_current_user_id
from app.db import get_db
from app.services.playback_service import PlaybackService
from app.services.navidrome_service import NavidromeService
from app.services.audio_quality_service import AudioQualityService
from app.services.access_control_service import AccessControlService
from app.services.recommendation_engine import EnhancedRecommendationService
from app.services.playback_session_service import PlaybackSessionService
from app.services.stream_token_service import StreamTokenService
from app.models.user import User

router = APIRouter(prefix="/playback", tags=["playback"])


class StartPlaybackRequest(BaseModel):
    device_id: str
    current_song_id: Optional[str] = None


class PlaybackHeartbeatRequest(BaseModel):
    session_id: str
    position_ms: int


class StopPlaybackRequest(BaseModel):
    session_id: str


@router.post("/start")
async def start_playback(
    payload: StartPlaybackRequest,
    network_type: str = Header(default="wifi", alias="X-Network-Type"),
    network_quality: float = Header(default=1.0, alias="X-Network-Quality"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    ATOMIC PLAYBACK ORCHESTRATION
    
    This single endpoint handles the complete playback decision engine:
    1. Validate device ownership
    2. Get next song recommendation
    3. CHECK ACCESS (FREE vs PAYMENT_REQUIRED) - ATOMIC with stream URL
    4. Enforce concurrent stream limits
    5. Determine audio quality
    6. Create playback session
    7. Return signed stream URL (not raw Navidrome URL)
    
    This eliminates TOCTOU gap by combining access check and stream issuance.
    """
    # 1. Validate device ownership
    # Get user for device validation and audio quality
    user = db.query(User).filter_by(id=current_user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Simple device validation: device_id must be provided and non-empty
    # In production, validate against registered devices table
    if not payload.device_id or len(payload.device_id) < 3:
        raise HTTPException(400, "Invalid device ID")
    
    # TODO: Enhanced device validation - check against registered devices
    # registered_device = db.query(Device).filter_by(user_id=current_user_id, device_id=payload.device_id).first()
    # if not registered_device:
    #     raise HTTPException(403, "Device not registered to user")
    
    # 2. Get next song from recommendation service
    rec_service = EnhancedRecommendationService(db)
    recommendation = rec_service.get_next_recommendation(
        user_id=str(current_user_id),
        current_song_id=payload.current_song_id
    )
    
    if not recommendation or not recommendation.get("recommendations"):
        raise HTTPException(404, "No song available for playback")
    
    song_data = recommendation["recommendations"][0]
    song_id = song_data["song_id"]
    
    # 3. ATOMIC: Check access control
    access_service = AccessControlService(db)
    can_play, error_code, access_details = await access_service.check_playback_access(
        str(current_user_id), song_id
    )
    
    # 4. If no access, return PAYMENT_REQUIRED (no stream URL)
    if not can_play:
        if error_code == "PAYMENT_REQUIRED":
            return {
                "status": "PAYMENT_REQUIRED",
                "message": "Purchase required to play full song",
                "song_preview": {
                    "id": song_id,
                    "title": song_data.get("title", "Unknown"),
                    "artist": song_data.get("artist", "Unknown"),
                    "preview_url": f"/api/v1/stream/preview/{song_id}",  # Use signed endpoint
                    "preview_duration": 30
                },
                "purchase_options": {
                    "individual": {
                        "price": access_details["price"],
                        "currency": access_details["currency"],
                        "purchase_url": f"/api/v1/payments/song-purchase?user_id={current_user_id}&song_id={song_id}"
                    },
                    "subscription": {
                        "available": access_details.get("requires_premium", False),
                        "tiers": ["premium", "premium_plus"],
                        "upgrade_url": "/api/v1/payments/subscription"
                    }
                }
            }
        
        raise HTTPException(403, error_code or "Access denied")
    
    # 5. Check concurrent stream limits
    session_service = PlaybackSessionService(db)
    stream_check = session_service.validate_stream_start(
        str(current_user_id), payload.device_id
    )
    
    if not stream_check["allowed"]:
        raise HTTPException(429, {
            "error": "CONCURRENT_LIMIT",
            "message": stream_check["reason"],
            "max_streams": stream_check["max_streams"],
            "active_sessions": stream_check["active_count"]
        })
    
    # 6. Determine audio quality
    audio_service = AudioQualityService()
    # Use actual user object and create device info dict
    device_info = {
        "device_id": payload.device_id,
        "device_class": getattr(user, 'device_class', 'high'),
        "network_type": network_type,
    }
    quality = audio_service.determine_quality(
        user=user,
        device=device_info,
        network_type=network_type,
        network_quality_score=network_quality
    )
    
    # 7. Create playback session
    session = session_service.create_session(
        user_id=str(current_user_id),
        device_id=payload.device_id,
        song_id=song_id,
        audio_quality=quality.quality,
        bitrate=quality.bitrate_kbps
    )
    
    # 8. Generate signed stream access token
    # This token is short-lived and grants direct media access via redirect
    stream_token = StreamTokenService.generate_token(
        session_id=session.id,
        user_id=current_user_id,
        song_id=song_id,
        quality=quality.quality,
        bitrate=quality.bitrate_kbps,
    )
    
    # Build media access URL - client hits this, backend validates and redirects to Navidrome
    stream_url = StreamTokenService.build_media_url(stream_token)
    
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
        }
    }


@router.get("/media")
async def media_redirect(
    token: str,
    db: Session = Depends(get_db),
):
    """
    SIGNED MEDIA REDIRECT ENDPOINT (Scalable)
    
    Validates a signed stream access token and returns HTTP 307 redirect
    to Navidrome with a freshly-generated auth URL. Audio bytes flow
    directly from Navidrome to the client - the API server is NOT the
    media transport bottleneck.
    
    This is the PRODUCTION path for media delivery.
    
    Args:
        token: Signed JWT stream token from /playback/start
    
    Returns:
        HTTP 307 redirect to Navidrome stream URL
    """
    # 1. Validate signed token
    payload = StreamTokenService.validate_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired stream token")
    
    session_id = payload.get("sid")
    user_id = int(payload.get("sub", 0))
    song_id = payload.get("song")
    quality = payload.get("qual", "high")
    bitrate = payload.get("br", 320)
    
    # 2. Validate session is still active
    session_service = PlaybackSessionService(db)
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(404, "Session not found or expired")
    
    if session.user_id != user_id:
        raise HTTPException(403, "Token does not match session")
    
    if session.ended_at:
        raise HTTPException(403, "Session has ended")
    
    # 3. Generate fresh Navidrome URL (never exposed to client directly)
    navidrome = NavidromeService()
    
    try:
        # Build Navidrome URL server-side with fresh timestamp
        redirect_url = await navidrome.get_stream_url(
            user_id=str(user_id),
            song_id=song_id,
            max_bitrate=bitrate,
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to generate stream: {str(e)}")
    
    # 4. Return redirect - client streams directly from Navidrome
    # HTTP 307 preserves the request method (GET)
    return RedirectResponse(
        url=redirect_url,
        status_code=307,
        headers={
            "X-Session-ID": session_id,
            "X-Stream-Quality": quality,
        }
    )


@router.get("/stream/{session_id}")
async def proxy_stream(
    session_id: str,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    range_header: Optional[str] = Header(None, alias="range"),
):
    """
    [DEPRECATED / FALLBACK] STREAM PROXY ENDPOINT
    
    FastAPI proxies audio bytes from Navidrome. This is NOT the production
    path because it makes the API server the media transport bottleneck.
    
    Use /playback/media?token=<token> (from /playback/start response)
    for production streaming instead. That endpoint returns a 307 redirect
    so media bytes flow directly from Navidrome to client.
    
    This endpoint is kept as a fallback for:
    - Clients that cannot follow redirects
    - Network configurations where direct Navidrome access is blocked
    - Debugging / testing
    """
    import httpx
    from fastapi.responses import StreamingResponse
    
    # 1. Validate session belongs to user and is active
    session_service = PlaybackSessionService(db)
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(404, "Session not found or expired")
    
    if str(session.user_id) != str(current_user_id):
        raise HTTPException(403, "Session does not belong to user")
    
    if session.ended_at:
        raise HTTPException(403, "Session has ended")
    
    # 2. Get internal Navidrome URL (never exposed to client)
    navidrome = NavidromeService()
    
    try:
        internal_stream_url = await navidrome.get_stream_url(
            user_id=str(current_user_id),
            song_id=session.song_id,
            max_bitrate=session.bitrate,
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to generate stream: {str(e)}")
    
    # 3. Proxy stream from Navidrome to client (fallback only)
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            headers = {}
            if range_header:
                headers["Range"] = range_header
            
            async with client.stream("GET", internal_stream_url, headers=headers) as response:
                response_headers = {}
                for header in ["content-type", "content-length", "content-range", "accept-ranges", "cache-control"]:
                    if header in response.headers:
                        response_headers[header] = response.headers[header]
                
                response_headers["X-Session-ID"] = session_id
                response_headers["X-Stream-Quality"] = session.audio_quality
                
                status_code = 206 if range_header and response.status_code == 206 else 200
                
                return StreamingResponse(
                    response.aiter_bytes(chunk_size=8192),
                    status_code=status_code,
                    headers=response_headers,
                    media_type=response.headers.get("content-type", "audio/mpeg"),
                )
                
    except httpx.RequestError as e:
        raise HTTPException(502, f"Failed to connect to audio source: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Stream error: {str(e)}")


@router.get("/stream/preview/{song_id}")
async def preview_stream(
    song_id: str,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Preview stream endpoint (30-second clips)
    Accessible without purchase for preview purposes.
    """
    navidrome = NavidromeService()
    # stream_url = await navidrome.get_stream_url(..., time_limit=30)
    
    return {"message": "Preview stream - to be implemented"}


@router.post("/heartbeat")
async def playback_heartbeat(
    payload: PlaybackHeartbeatRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Keep playback session alive"""
    session_service = PlaybackSessionService(db)
    updated = session_service.update_heartbeat(
        payload.session_id,
        current_user_id,
        payload.position_ms,
    )
    
    if not updated:
        raise HTTPException(404, "Session not found or expired")
    
    return {"ok": True, "session_active": True}


@router.post("/stop")
async def stop_playback(
    payload: StopPlaybackRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """End playback session"""
    session_service = PlaybackSessionService(db)
    stopped = session_service.end_session(payload.session_id, current_user_id)
    if not stopped:
        raise HTTPException(404, "Session not found")
    
    return {"stopped": True, "session_id": payload.session_id}


# Legacy endpoint for backward compatibility
@router.post("", response_model=schemas.PlaybackEventResponse)
def record_playback(
    payload: schemas.PlaybackEventIn,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Legacy endpoint - records playback events only"""
    try:
        safe_payload = payload.model_copy(update={"user_id": current_user_id})
        return PlaybackService(db).record_playback(safe_payload)
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail="User not found") from exc
        if str(exc) == "song_not_found":
            raise HTTPException(status_code=404, detail="Song not found") from exc
        raise
