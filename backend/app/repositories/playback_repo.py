from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from sqlalchemy import case, desc, distinct, func, inspect, text
from sqlalchemy.orm import Session, joinedload

from app import models
from app.utils.helpers import utc_now


class PlaybackRepository:
    """Handles playback events, sessions, and recommendation-facing aggregates."""

    def __init__(self, db: Session):
        self.db = db

    def get_recent_user_events(
        self,
        user_id: int,
        *,
        hours: int = 24 * 30,
        limit: int | None = None,
    ) -> list[models.PlaybackEvent]:
        cutoff = utc_now() - timedelta(hours=hours)
        query = (
            self.db.query(models.PlaybackEvent)
            .options(joinedload(models.PlaybackEvent.song))
            .filter(models.PlaybackEvent.user_id == user_id)
            .filter(models.PlaybackEvent.timestamp >= cutoff)
            .order_by(desc(models.PlaybackEvent.timestamp))
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def list_recent_events_for_user(
        self,
        user_id: int,
        *,
        hours: int = 24 * 30,
        limit: int | None = None,
    ) -> list[models.PlaybackEvent]:
        return self.get_recent_user_events(user_id, hours=hours, limit=limit)

    def list_recent_events(
        self,
        *,
        hours: int = 24 * 7,
    ) -> list[models.PlaybackEvent]:
        cutoff = utc_now() - timedelta(hours=hours)
        return (
            self.db.query(models.PlaybackEvent)
            .options(joinedload(models.PlaybackEvent.song))
            .filter(models.PlaybackEvent.timestamp >= cutoff)
            .all()
        )

    def create_event(self, event: models.PlaybackEvent) -> models.PlaybackEvent:
        self._ensure_event_table_columns()
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def create(self, event: models.PlaybackEvent) -> models.PlaybackEvent:
        return self.create_event(event)

    def get_active_session(
        self,
        user_id: int,
        *,
        max_idle_minutes: int = 30,
    ) -> models.PlaybackSession | None:
        cutoff = utc_now() - timedelta(minutes=max_idle_minutes)
        return (
            self.db.query(models.PlaybackSession)
            .filter(models.PlaybackSession.user_id == user_id)
            .filter(models.PlaybackSession.status == "active")
            .filter(models.PlaybackSession.last_activity_at >= cutoff)
            .order_by(desc(models.PlaybackSession.last_activity_at))
            .first()
        )

    def get_or_create_session(
        self,
        user_id: int,
        *,
        session_id: int | None = None,
    ) -> models.PlaybackSession:
        if session_id is not None:
            session = (
                self.db.query(models.PlaybackSession)
                .filter(models.PlaybackSession.id == session_id)
                .filter(models.PlaybackSession.user_id == user_id)
                .first()
            )
            if session is not None:
                session.last_activity_at = utc_now()
                session.ended_at = None
                session.status = "active"
                self.db.commit()
                self.db.refresh(session)
                return session

        session = self.get_active_session(user_id)
        if session is not None:
            session.last_activity_at = utc_now()
            self.db.commit()
            self.db.refresh(session)
            return session

        stale_sessions = (
            self.db.query(models.PlaybackSession)
            .filter(models.PlaybackSession.user_id == user_id)
            .filter(models.PlaybackSession.status == "active")
            .all()
        )
        for stale in stale_sessions:
            stale.status = "ended"
            stale.ended_at = utc_now()

        session = models.PlaybackSession(user_id=user_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_or_start_session(self, user_id: int) -> models.PlaybackSession:
        return self.get_or_create_session(user_id)

    def replace_session_recommendations(
        self,
        session_id: int,
        songs: list[tuple[str, float]],
    ) -> None:
        self.db.query(models.SessionRecommendationEvent).filter(
            models.SessionRecommendationEvent.session_id == session_id
        ).delete()

        for position, (song_id, score) in enumerate(songs, start=1):
            self.db.add(
                models.SessionRecommendationEvent(
                    session_id=session_id,
                    song_id=song_id,
                    position=position,
                    score=score,
                )
            )

        self.db.commit()

    def _ensure_event_table_columns(self) -> None:
        """Backfill required playback columns for older local SQLite databases."""
        bind = self.db.get_bind()
        inspector = inspect(bind)
        if "playback_events" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("playback_events")}
        with bind.begin() as connection:
            if "session_id" not in columns:
                connection.execute(text("ALTER TABLE playback_events ADD COLUMN session_id INTEGER"))
            if "event_type" not in columns:
                connection.execute(text("ALTER TABLE playback_events ADD COLUMN event_type VARCHAR(20)"))
            if "timestamp" not in columns:
                connection.execute(text("ALTER TABLE playback_events ADD COLUMN timestamp DATETIME"))

    def song_event_stats(
        self,
        song_ids: list[int] | None = None,
        *,
        hours: int = 24 * 30,
    ) -> dict[int, dict[str, float]]:
        cutoff = utc_now() - timedelta(hours=hours)
        query = (
            self.db.query(
                models.PlaybackEvent.song_id.label("song_id"),
                func.count(models.PlaybackEvent.id).label("plays"),
                func.sum(
                    case(
                        (models.PlaybackEvent.event_type == "complete", 1),
                        else_=0,
                    )
                ).label("completes"),
                func.sum(
                    case((models.PlaybackEvent.event_type == "skip", 1), else_=0)
                ).label("skips"),
                func.max(models.PlaybackEvent.timestamp).label("last_played_at"),
            )
            .filter(models.PlaybackEvent.timestamp >= cutoff)
            .group_by(models.PlaybackEvent.song_id)
        )
        if song_ids:
            query = query.filter(models.PlaybackEvent.song_id.in_(song_ids))

        results: dict[int, dict[str, float]] = {}
        for row in query.all():
            plays = int(row.plays or 0)
            completes = int(row.completes or 0)
            skips = int(row.skips or 0)
            results[int(row.song_id)] = {
                "play_count": float(plays),
                "completion_rate": (completes / plays) if plays else 0.0,
                "skip_rate": (skips / plays) if plays else 0.0,
                "last_played_at": row.last_played_at,
            }
        return results

    def trending_song_ids(self, *, limit: int = 50, hours: int = 24 * 7) -> list[int]:
        cutoff = utc_now() - timedelta(hours=hours)
        rows = (
            self.db.query(
                models.PlaybackEvent.song_id,
                func.count(models.PlaybackEvent.id).label("play_count"),
            )
            .filter(models.PlaybackEvent.timestamp >= cutoff)
            .group_by(models.PlaybackEvent.song_id)
            .order_by(desc("play_count"))
            .limit(limit)
            .all()
        )
        return [int(song_id) for song_id, _play_count in rows]

    def user_top_song_ids(self, user_id: int, *, limit: int = 30) -> list[int]:
        rows = (
            self.db.query(
                models.PlaybackEvent.song_id,
                func.count(models.PlaybackEvent.id).label("play_count"),
            )
            .filter(models.PlaybackEvent.user_id == user_id)
            .group_by(models.PlaybackEvent.song_id)
            .order_by(desc("play_count"))
            .limit(limit)
            .all()
        )
        return [int(song_id) for song_id, _play_count in rows]

    def distinct_recent_artists(self, user_id: int, *, limit: int = 5) -> list[str]:
        rows = (
            self.db.query(distinct(models.LibrarySong.artist))
            .join(models.PlaybackEvent, models.PlaybackEvent.song_id == models.LibrarySong.id)
            .filter(models.PlaybackEvent.user_id == user_id)
            .order_by(desc(models.PlaybackEvent.timestamp))
            .limit(limit)
            .all()
        )
        return [artist for (artist,) in rows if artist]

    def recently_skipped_song_ids(
        self,
        user_id: int,
        *,
        hours: int = 24,
        limit: int = 25,
    ) -> set[int]:
        cutoff = utc_now() - timedelta(hours=hours)
        rows = (
            self.db.query(models.PlaybackEvent.song_id)
            .filter(models.PlaybackEvent.user_id == user_id)
            .filter(models.PlaybackEvent.event_type == "skip")
            .filter(models.PlaybackEvent.timestamp >= cutoff)
            .order_by(desc(models.PlaybackEvent.timestamp))
            .limit(limit)
            .all()
        )
        return {int(song_id) for (song_id,) in rows}
