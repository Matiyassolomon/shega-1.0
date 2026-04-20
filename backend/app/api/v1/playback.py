from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.core.security import get_current_user_id
from app.db import get_db
from app.services.playback_service import PlaybackService

router = APIRouter(prefix="/playback", tags=["playback"])


@router.post("", response_model=schemas.PlaybackEventResponse)
def record_playback(
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
        if str(exc) == "song_not_found":
            raise HTTPException(status_code=404, detail="Song not found") from exc
        raise
