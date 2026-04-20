from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PlaybackEventType = Literal["play", "skip", "complete"]


class PlaybackEventCreate(BaseModel):
    song_id: str = Field(..., min_length=1, max_length=255)
    session_id: int | None = Field(default=None, ge=1)


class PlaybackEventResponse(BaseModel):
    recorded: bool
    event_id: int | None = None
    session_id: int | None = None
    event_type: PlaybackEventType | None = None
    song_id: str
    timestamp: datetime | None = None
    user_id: int | None = None
    updated_taste_vector: dict[str, object] | None = None
