from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import schemas
from app.core.auth import create_access_token, get_current_user_id
from app.db import get_db
from app.services import crud
from app.services.playback_service import PlaybackService

router = APIRouter(tags=["core"])


@router.post("/register-device", response_model=schemas.RegisterDeviceResponse)
def register_device(
    payload: schemas.DeviceRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    telegram_detected = crud.is_telegram_request(
        payload.telegram, dict(request.headers)
    )
    user = crud.create_user(db, payload, telegram_detected)
    return {
        "access_token": create_access_token(user.id),
        "device_class": user.device_class,
        "token_type": "bearer",
        "user_id": user.id,
    }


@router.get("/users/{user_id}/profile", response_model=schemas.UserProfileResponse)
def user_profile(user_id: int, db: Session = Depends(get_db)):
    try:
        return crud.get_user_profile(db, user_id)
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail="User not found") from exc
        raise


@router.get("/subscription/check", response_model=schemas.SubscriptionCheckResponse)
def subscription_check(user_id: int, db: Session = Depends(get_db)):
    return crud.get_subscription_status(db, user_id)


@router.post("/engagement/playback", response_model=schemas.PlaybackEventResponse)
def log_playback(
    payload: schemas.PlaybackEventIn,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        safe_payload = payload.model_copy(update={"user_id": current_user_id})
        return PlaybackService(db).record_playback(safe_payload)
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail="User not found") from exc
        raise


@router.get("/can-play/{song_id}/{user_id}", response_model=schemas.CanPlayResponse)
def can_play(song_id: str, user_id: int, db: Session = Depends(get_db)):
    allowed = crud.can_user_play_song(db, song_id, user_id)
    return {"allowed": allowed}


@router.get("/premium-songs", response_model=list[str])
def premium_songs(db: Session = Depends(get_db)):
    return crud.list_premium_song_ids(db)


@router.get("/stream-policy/{user_id}", response_model=schemas.StreamPolicyResponse)
def stream_policy(user_id: int, db: Session = Depends(get_db)):
    try:
        return crud.get_stream_policy(db, user_id)
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail="User not found") from exc
        raise
