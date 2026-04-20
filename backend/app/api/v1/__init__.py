from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.events import router as events_router
from app.api.v1.health import router as health_router
from app.api.v1.playback import router as playback_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.songs import router as songs_router
from app.api.v1.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(events_router)
api_router.include_router(health_router)
api_router.include_router(users_router)
api_router.include_router(songs_router)
api_router.include_router(playback_router)
api_router.include_router(recommendations_router)

__all__ = ["api_router"]
