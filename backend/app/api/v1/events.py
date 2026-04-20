from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.core.security import get_current_user_id
from app.db import get_db
from app.services.playback_service import PlaybackService

router = APIRouter(prefix="/events", tags=["events"])


def _record_event(
    event_type: schemas.PlaybackEventType,
    payload: schemas.PlaybackEventCreate,
    current_user_id: int,
    db: Session,
) -> schemas.PlaybackEventResponse:
    try:
        return PlaybackService(db).record_event(
            user_id=current_user_id,
            payload=payload,
            event_type=event_type,
        )
    except ValueError as exc:
        message = str(exc)
        if message == "song_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found") from exc
        if message == "user_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found") from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid playback event") from exc


@router.post("/play", response_model=schemas.PlaybackEventResponse, status_code=status.HTTP_201_CREATED)
def record_play(
    payload: schemas.PlaybackEventCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return _record_event("play", payload, current_user_id, db)


@router.post("/skip", response_model=schemas.PlaybackEventResponse, status_code=status.HTTP_201_CREATED)
def record_skip(
    payload: schemas.PlaybackEventCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return _record_event("skip", payload, current_user_id, db)


@router.post("/complete", response_model=schemas.PlaybackEventResponse, status_code=status.HTTP_201_CREATED)
def record_complete(
    payload: schemas.PlaybackEventCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return _record_event("complete", payload, current_user_id, db)
