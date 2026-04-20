from __future__ import annotations

from sqlalchemy.orm import Session

from app import models, schemas
from app.repositories.playback_repo import PlaybackRepository
from app.repositories.song_repo import SongRepository
from app.repositories.user_repo import UserRepository
from app.services import crud
from app.utils.helpers import utc_now


class PlaybackService:
    """Records user playback events without trusting client-supplied user identifiers."""

    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.songs = SongRepository(db)
        self.playback = PlaybackRepository(db)

    def record_event(
        self,
        *,
        user_id: int,
        payload: schemas.PlaybackEventCreate,
        event_type: schemas.PlaybackEventType,
    ) -> schemas.PlaybackEventResponse:
        """Persist a normalized playback event and keep song aggregates fresh."""
        user = self.users.get_by_id(user_id)
        if user is None:
            raise ValueError("user_not_found")

        song = self.songs.get_by_navidrome_id(payload.song_id)
        if song is None:
            raise ValueError("song_not_found")

        session = self.playback.get_or_create_session(user_id, session_id=payload.session_id)
        event = models.PlaybackEvent(
            user_id=user_id,
            song_id=song.id,
            session_id=session.id,
            event_type=event_type,
            timestamp=utc_now(),
            completed_ratio=1.0 if event_type == "complete" else 0.0,
            skipped=event_type == "skip",
            weight=1.0 if event_type == "play" else (0.3 if event_type == "skip" else 1.5),
        )
        saved_event = self.playback.create_event(event)
        self._refresh_song_aggregates(song)
        return schemas.PlaybackEventResponse(
            recorded=True,
            event_id=saved_event.id,
            session_id=session.id,
            event_type=event_type,
            song_id=song.navidrome_song_id,
            timestamp=saved_event.timestamp,
            user_id=user_id,
        )

    def record_playback(self, payload: schemas.PlaybackEventIn) -> schemas.PlaybackEventResponse:
        """Compatibility wrapper for the legacy playback route."""
        user = self.users.get_by_id(payload.user_id)
        if user is None:
            raise ValueError("user_not_found")

        song = self.songs.get_by_navidrome_id(payload.song_id)
        if song is None:
            song = crud.get_or_create_song_from_event(self.db, payload)

        session = self.playback.get_or_create_session(payload.user_id)
        event_type: schemas.PlaybackEventType = "skip" if payload.skipped else (
            "complete" if payload.completed_ratio >= 0.85 else "play"
        )
        saved_event = self.playback.create_event(
            models.PlaybackEvent(
                user_id=payload.user_id,
                song_id=song.id,
                session_id=session.id,
                event_type=event_type,
                timestamp=utc_now(),
                location=payload.location,
                completed_ratio=payload.completed_ratio,
                played_seconds=payload.played_seconds,
                is_looped=payload.is_looped,
                skipped=payload.skipped,
                weight=crud._engagement_weight(payload),
            )
        )
        self._refresh_song_aggregates(song)
        vector = crud.refresh_user_taste_vector(self.db, payload.user_id)
        return schemas.PlaybackEventResponse(
            recorded=True,
            event_id=saved_event.id,
            session_id=session.id,
            event_type=event_type,
            song_id=song.navidrome_song_id,
            timestamp=saved_event.timestamp,
            user_id=payload.user_id,
            updated_taste_vector=crud._taste_vector_schema(vector).model_dump(),
        )

    def _refresh_song_aggregates(self, song: models.LibrarySong) -> None:
        """Update denormalized counters used by the ranking layer."""
        stats = self.playback.song_event_stats([song.id]).get(song.id, {})
        play_count = int(stats.get("play_count", 0.0))
        completion_rate = float(stats.get("completion_rate", 0.0))
        skip_rate = float(stats.get("skip_rate", 0.0))

        song.play_count_7d = play_count
        song.like_count_7d = int(round(play_count * completion_rate))
        song.skip_rate = round(skip_rate, 4)
        self.db.commit()
        self.db.refresh(song)
