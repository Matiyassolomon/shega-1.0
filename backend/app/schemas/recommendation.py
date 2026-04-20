from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RecommendationBreakdown(BaseModel):
    completion_rate: float
    skip_rate: float
    popularity: float
    recency: float
    diversity_adjustment: float
    session_penalty: float


class RecommendationSong(BaseModel):
    song_id: str
    title: str
    artist: str
    genre: str
    stream_url: str | None = None
    score: float
    reasons: list[str] = Field(default_factory=list)
    breakdown: RecommendationBreakdown
    source: str = "internal"
    source_metadata: dict[str, Any] = Field(default_factory=dict)


class RecommendationHomeResponse(BaseModel):
    generated_at: datetime
    recommendations: list[RecommendationSong]


class RecommendationNextResponse(BaseModel):
    generated_at: datetime
    current_song_id: str
    recommendations: list[RecommendationSong]


class TrendingSongResponse(BaseModel):
    song_id: str
    title: str
    artist: str
    genre: str
    stream_url: str | None = None
    play_count: int
    completion_rate: float
    skip_rate: float
    hot_score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrendingResponse(BaseModel):
    generated_at: datetime
    recommendations: list[TrendingSongResponse]
