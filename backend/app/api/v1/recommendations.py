from collections import defaultdict
from time import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app import schemas
from app.core.auth import bearer_scheme, decode_access_token
from app.core.security import get_current_user_id
from app.core.settings import get_settings
from app.db import get_db
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
_REQUEST_LOG: dict[str, list[float]] = defaultdict(list)


def _recommendation_rate_limit(request: Request) -> None:
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    now = time()
    window = _REQUEST_LOG[client_ip]
    window[:] = [stamp for stamp in window if now - stamp < 60]
    if len(window) >= settings.recommendation_rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Recommendation rate limit exceeded",
        )
    window.append(now)


@router.get("/home", response_model=schemas.RecommendationHomeResponse)
def home_recommendations(
    request: Request,
    limit: int = Query(default=12, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _recommendation_rate_limit(request)
    try:
        return RecommendationService(db).get_home_recommendations(
            user_id=current_user_id,
            limit=limit,
        )
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail="User not found") from exc
        raise


@router.get("/next", response_model=schemas.RecommendationNextResponse)
def next_recommendations(
    request: Request,
    song_id: str = Query(..., min_length=1),
    limit: int = Query(default=8, ge=1, le=25),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _recommendation_rate_limit(request)
    try:
        return RecommendationService(db).get_next_recommendations(
            user_id=current_user_id,
            song_id=song_id,
            limit=limit,
        )
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail="User not found") from exc
        if str(exc) == "song_not_found":
            raise HTTPException(status_code=404, detail="Song not found") from exc
        raise


@router.get("/trending", response_model=schemas.TrendingResponse)
def trending_recommendations(
    request: Request,
    limit: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    _recommendation_rate_limit(request)
    return RecommendationService(db).get_trending_recommendations(limit=limit)


@router.get("/feed", response_model=schemas.PersonalizedFeedResponse)
def personalized_feed(
    request: Request,
    user_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=12, ge=1, le=50),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    _recommendation_rate_limit(request)
    try:
        resolved_user_id = user_id
        if credentials is not None and credentials.scheme.lower() == "bearer":
            resolved_user_id = int(decode_access_token(credentials.credentials)["sub"])
        if resolved_user_id is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        return RecommendationService(db).get_personalized_feed(
            user_id=resolved_user_id,
            limit=limit,
        )
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail="User not found") from exc
        raise
