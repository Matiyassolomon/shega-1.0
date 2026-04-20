from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.db import get_db
from app.schemas.recommendation import get_next_song
from app.core.security import get_current_user_id

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/next", response_model=schemas.RecommendationNextResponse)
def next_song(
    song_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    song = get_next_song(db, user_id, song_id)

    if not song:
        raise HTTPException(status_code=404, detail="No recommendation found")

    return song