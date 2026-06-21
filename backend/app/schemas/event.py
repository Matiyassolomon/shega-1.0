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

    id: int | None = None
    event_id: int | None = None
    recorded: bool = True
    user_id: int
    song_id: int | str
    event_type: str | None = None
    session_id: int | str | None = None
    timestamp: datetime | None = None
    updated_taste_vector: dict | None = None
