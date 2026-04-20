from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict

PlaybackEventType = Literal["play", "skip", "complete"]

class PlaybackEventCreate(BaseModel):
    song_id: int
    event_type: PlaybackEventType
    session_id: Optional[str] = None

class PlaybackEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    song_id: int
    event_type: str
    session_id: Optional[str] = None
    timestamp: datetime