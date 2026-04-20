from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.event import PlaybackEventCreate, PlaybackEventResponse, PlaybackEventType
from app.schemas.recommendation import (
    RecommendationBreakdown,
    RecommendationHomeResponse,
    RecommendationNextResponse,
    RecommendationSong,
    TrendingResponse,
    TrendingSongResponse,
)

DeviceClass = Literal["lite", "standard", "high"]
SubscriptionStatus = Literal["active", "expired"]
PaymentMethod = Literal["telebirr", "cbe"]
PaymentStatus = Literal["pending", "confirmed"]


class DeviceRegister(BaseModel):
    user_agent: str = Field(..., min_length=1)
    telegram: bool = False
    telegram_id: str | None = None
    email: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: str | None
    email: str | None
    device_class: DeviceClass
    is_telegram_user: bool
    created_at: datetime


class RegisterDeviceResponse(BaseModel):
    user_id: int
    device_class: DeviceClass
    access_token: str
    token_type: str = "bearer"


class CanPlayResponse(BaseModel):
    allowed: bool


class StreamPolicyResponse(BaseModel):
    device_class: DeviceClass
    maxBitrate: int


class SubscriptionCheckResponse(BaseModel):
    subscribed: bool
    status: SubscriptionStatus
    expires_at: datetime | None = None


class PremiumSongOut(BaseModel):
    navidrome_song_id: str


class SellPlaylistRequest(BaseModel):
    playlist_id: str
    seller_id: int
    price: float = Field(..., gt=0)
    currency: str = "ETB"
    is_public: bool = True


class SellSongRequest(BaseModel):
    song_id: str
    seller_id: int
    price: float = Field(..., gt=0)
    currency: str = "ETB"
    is_public: bool = True


class MarketplaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    playlist_id: str
    seller_id: int
    price: float
    currency: str
    sales_count: int
    is_public: bool


class MarketplacePlaylistOut(BaseModel):
    playlist_id: str
    title: str
    creator_name: str
    artist_name: str | None
    artist_verified: bool
    price: float
    currency: str
    sales_count: int
    save_count: int
    share_count: int
    save_rate: float
    social_score: float
    region: str | None
    preview_song_id: str | None
    cover_art_path: str | None


class MarketplaceSongOut(BaseModel):
    song_id: str
    title: str
    artist: str
    genre: str
    price: float
    currency: str
    sales_count: int
    play_count_7d: int
    like_count_7d: int
    cover_art_path: str | None
    is_premium: bool


class BuyPlaylistRequest(BaseModel):
    playlist_id: str
    buyer_id: int


class BuyPlaylistResponse(BaseModel):
    playlist_id: str
    buyer_id: int
    sales_count: int
    purchased: bool


class BuySongRequest(BaseModel):
    song_id: str
    buyer_id: int


class BuySongResponse(BaseModel):
    song_id: str
    buyer_id: int
    sales_count: int
    purchased: bool


class SavePlaylistRequest(BaseModel):
    playlist_id: str
    user_id: int


class SavePlaylistResponse(BaseModel):
    playlist_id: str
    save_count: int
    saved: bool


class SecurePlaylistAccessResponse(BaseModel):
    playlist_id: str
    authorized: bool
    x_accel_redirect: str | None = None
    art_redirect: str | None = None
    stream_path: str | None = None
    art_path: str | None = None


class SecureSongAccessResponse(BaseModel):
    song_id: str
    authorized: bool
    stream_path: str | None = None
    art_path: str | None = None


class PaymentCreateRequest(BaseModel):
    user_id: int
    amount: float = Field(..., gt=0)
    method: PaymentMethod
    payment_type: Literal[
        "playlist_purchase",
        "song_purchase",
        "subscription_monthly",
        "wallet_topup",
    ] = "subscription_monthly"
    playlist_id: str | None = None


class PaymentConfirmRequest(BaseModel):
    payment_id: int


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    amount: float
    method: PaymentMethod
    status: PaymentStatus
    payment_type: str | None = None
    playlist_id: str | None = None
    created_at: datetime


class PaymentConfirmResponse(BaseModel):
    payment_id: int
    status: PaymentStatus
    subscription_status: SubscriptionStatus
    expires_at: datetime


class GregorianDateIn(BaseModel):
    year: int
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)


class EthiopianDateIn(BaseModel):
    year: int
    month: int = Field(..., ge=1, le=13)
    day: int = Field(..., ge=1, le=30)


class EthiopianDateOut(BaseModel):
    year: int
    month: int
    day: int


class PlaylistRecommendation(BaseModel):
    playlist_id: str
    title: str
    reason: str
    tags: list[str]


class PlaylistRecommendationResponse(BaseModel):
    date: str
    holiday: str | None
    recommendations: list[PlaylistRecommendation]


class TasteVectorOut(BaseModel):
    qenet_mode_affinity: dict[str, float]
    genre_affinity: dict[str, float]
    average_tempo: float
    acoustic_signature: dict[str, float]


class LookalikeUserOut(BaseModel):
    user_id: int
    similarity: float


class PersonalizedFeedResponse(BaseModel):
    user_id: int
    location: str | None
    model_backend: str
    taste_vector: TasteVectorOut
    lookalike_audience: list[LookalikeUserOut]
    recommendations: list[RecommendationSong]


class PlaybackEventIn(BaseModel):
    user_id: int | None = None
    song_id: str
    title: str = ""
    artist: str = ""
    genre: str = "Unknown"
    country: str | None = None
    language: str | None = None
    qenet_mode: str | None = None
    release_date: str | None = None
    tempo: float = 0
    duration: float = 0
    played_seconds: float = Field(default=0, ge=0)
    completed_ratio: float = Field(default=0, ge=0, le=2)
    skipped: bool = False
    is_looped: bool = False
    location: str | None = None
    playlist_id: str | None = None
    extracted_features: dict[str, object] = Field(default_factory=dict)


class HybridRecommendationResponse(BaseModel):
    date: str
    holiday: str | None
    location: str | None
    model_backend: str
    recommendations: list[RecommendationSong]


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: str | None
    email: str | None
    device_class: DeviceClass
    is_telegram_user: bool
    created_at: datetime
    preferred_location: str | None = None
    active_subscription: bool
    subscription_status: SubscriptionStatus
    expires_at: datetime | None = None
    taste_vector: TasteVectorOut
    lookalike_audience: list[LookalikeUserOut]
    recent_playback_count: int
    secure_playlist_ids: list[str]


class AudioAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    genre: str = Field(alias="Genre")
    qenet_mode: str = Field(alias="Qenet Mode")
    tempo: float = Field(alias="Tempo")


class HolidayRuleBase(BaseModel):
    key: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    eth_month: int = Field(..., ge=1, le=13)
    eth_day: int = Field(..., ge=1, le=30)
    recommendations: list[PlaylistRecommendation]
    is_active: bool = True


class HolidayRuleCreate(HolidayRuleBase):
    pass


class HolidayRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    eth_month: int | None = Field(default=None, ge=1, le=13)
    eth_day: int | None = Field(default=None, ge=1, le=30)
    recommendations: list[PlaylistRecommendation] | None = None
    is_active: bool | None = None


class HolidayRuleOut(HolidayRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


SongRecommendationOut = RecommendationSong
TrendingSongOut = TrendingSongResponse
TrendingFeedResponse = TrendingResponse


__all__ = [
    "AudioAnalysisResponse",
    "BuyPlaylistRequest",
    "BuyPlaylistResponse",
    "BuySongRequest",
    "BuySongResponse",
    "CanPlayResponse",
    "DeviceRegister",
    "EthiopianDateIn",
    "EthiopianDateOut",
    "GregorianDateIn",
    "HolidayRuleCreate",
    "HolidayRuleOut",
    "HolidayRuleUpdate",
    "HybridRecommendationResponse",
    "LookalikeUserOut",
    "MarketplaceOut",
    "MarketplacePlaylistOut",
    "MarketplaceSongOut",
    "PaymentConfirmRequest",
    "PaymentConfirmResponse",
    "PaymentCreateRequest",
    "PaymentOut",
    "PlaybackEventIn",
    "PlaybackEventCreate",
    "PlaybackEventResponse",
    "PlaybackEventType",
    "PlaylistRecommendation",
    "PlaylistRecommendationResponse",
    "PremiumSongOut",
    "RecommendationBreakdown",
    "RecommendationHomeResponse",
    "RecommendationNextResponse",
    "RecommendationSong",
    "RegisterDeviceResponse",
    "SavePlaylistRequest",
    "SavePlaylistResponse",
    "SecurePlaylistAccessResponse",
    "SecureSongAccessResponse",
    "SellPlaylistRequest",
    "SellSongRequest",
    "StreamPolicyResponse",
    "SubscriptionCheckResponse",
    "TasteVectorOut",
    "TrendingFeedResponse",
    "TrendingResponse",
    "TrendingSongOut",
    "TrendingSongResponse",
    "UserOut",
    "UserProfileResponse",
]
