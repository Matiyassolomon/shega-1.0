from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from math import exp

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.settings import get_settings
from app.repositories.recommendation_repo import RecommendationRepository
from app.utils.cache import CacheClient


@dataclass
class TasteVector:
    qenet_mode_affinity: dict[str, float]
    genre_affinity: dict[str, float]
    average_tempo: float
    acoustic_signature: dict[str, float]


@dataclass
class RankedSong:
    song: models.LibrarySong
    score: float
    reasons: list[str]
    breakdown: schemas.RecommendationBreakdown


class FastRecommendationLayer:
    """Layer 1: generate a broad but relevant candidate set."""

    def __init__(self, repository: RecommendationRepository):
        self.repository = repository

    def get_candidate_songs(
        self,
        *,
        user_id: int,
        current_song_id: str | None = None,
        limit: int = 120,
    ) -> list[models.LibrarySong]:
        """Collect candidates from artist, genre, history, and trending sources."""
        song_map: dict[int, models.LibrarySong] = {}

        user_top_song_ids = self.repository.playback.user_top_song_ids(user_id, limit=20)
        listened_songs = (
            self.repository.db.query(models.LibrarySong)
            .filter(models.LibrarySong.id.in_(user_top_song_ids))
            .all()
            if user_top_song_ids
            else []
        )
        listened_genres = {song.genre for song in listened_songs if song.genre}
        listened_artists = {song.artist for song in listened_songs if song.artist}

        if current_song_id:
            current_song = self.repository.songs.get_by_navidrome_id(current_song_id)
            if current_song is not None:
                listened_genres.add(current_song.genre)
                listened_artists.add(current_song.artist)

        if listened_genres or listened_artists:
            conditions = []
            if listened_genres:
                conditions.append(models.LibrarySong.genre.in_(list(listened_genres)))
            if listened_artists:
                conditions.append(models.LibrarySong.artist.in_(list(listened_artists)))
            content_candidates = (
                self.repository.db.query(models.LibrarySong)
                .filter(or_(*conditions))
                .order_by(desc(models.LibrarySong.play_count_7d), desc(models.LibrarySong.like_count_7d))
                .limit(limit)
                .all()
            )
            for song in content_candidates:
                song_map[song.id] = song

        for song in listened_songs:
            if song.genre:
                neighbors = (
                    self.repository.db.query(models.LibrarySong)
                    .filter(models.LibrarySong.genre == song.genre)
                    .order_by(desc(models.LibrarySong.play_count_7d))
                    .limit(12)
                    .all()
                )
                for neighbor in neighbors:
                    song_map[neighbor.id] = neighbor
            if song.artist:
                neighbors = (
                    self.repository.db.query(models.LibrarySong)
                    .filter(models.LibrarySong.artist == song.artist)
                    .order_by(desc(models.LibrarySong.play_count_7d))
                    .limit(12)
                    .all()
                )
                for neighbor in neighbors:
                    song_map[neighbor.id] = neighbor

        trending_ids = self.repository.playback.trending_song_ids(limit=30)
        if trending_ids:
            trending_songs = (
                self.repository.db.query(models.LibrarySong)
                .filter(models.LibrarySong.id.in_(trending_ids))
                .all()
            )
            for song in trending_songs:
                song_map[song.id] = song

        if not song_map:
            for song in self.repository.songs.list_catalog(limit=limit):
                song_map[song.id] = song

        return list(song_map.values())[:limit]


class RankingEngine:
    """Layer 2: score candidates using engagement and freshness signals."""

    def __init__(self, repository: RecommendationRepository):
        self.repository = repository

    def rank_songs(
        self,
        *,
        user_id: int,
        candidates: list[models.LibrarySong],
    ) -> list[RankedSong]:
        """Score each candidate by completion, skip, popularity, and recency."""
        if not candidates:
            return []

        stats = self.repository.playback.song_event_stats([song.id for song in candidates])
        ranked: list[RankedSong] = []
        for song in candidates:
            song_stats = stats.get(song.id, {})
            completion_rate = float(song_stats.get("completion_rate", 0.0))
            skip_rate = float(song_stats.get("skip_rate", song.skip_rate))
            play_count = float(song_stats.get("play_count", song.play_count_7d))
            recency = self._recency_score(song_stats.get("last_played_at"), song.release_date)

            score = (
                completion_rate * 45.0
                + (1.0 - min(skip_rate, 1.0)) * 25.0
                + min(play_count / 10.0, 20.0)
                + recency * 10.0
            )
            ranked.append(
                RankedSong(
                    song=song,
                    score=round(score, 4),
                    reasons=self._build_reasons(song, completion_rate, skip_rate, play_count),
                    breakdown=schemas.RecommendationBreakdown(
                        completion_rate=round(completion_rate, 4),
                        skip_rate=round(skip_rate, 4),
                        popularity=round(min(play_count / 10.0, 20.0), 4),
                        recency=round(recency * 10.0, 4),
                        diversity_adjustment=0.0,
                        session_penalty=0.0,
                    ),
                )
            )

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked

    def _recency_score(self, last_played_at: datetime | None, release_date: str | None) -> float:
        """Prefer songs with fresh engagement or recent release dates."""
        if last_played_at is not None:
            if last_played_at.tzinfo is None:
                last_played_at = last_played_at.replace(tzinfo=UTC)
            age_hours = max((datetime.now(UTC) - last_played_at).total_seconds() / 3600, 0.0)
            return exp(-age_hours / 72.0)

        if release_date:
            try:
                released_on = datetime.strptime(release_date, "%Y-%m-%d").date()
            except ValueError:
                return 0.0
            age_days = max((date.today() - released_on).days, 0)
            return exp(-age_days / 30.0)
        return 0.0

    def _build_reasons(
        self,
        song: models.LibrarySong,
        completion_rate: float,
        skip_rate: float,
        play_count: float,
    ) -> list[str]:
        """Explain recommendation decisions in a compact, stable way."""
        reasons: list[str] = []
        if completion_rate >= 0.6:
            reasons.append("high completion rate")
        if skip_rate <= 0.2:
            reasons.append("low skip rate")
        if play_count >= 10:
            reasons.append("trending with listeners")
        if song.genre:
            reasons.append(f"genre match: {song.genre}")
        return reasons[:4]


class SessionOptimizer:
    """Layer 3: improve session flow and reduce fatigue."""

    def __init__(self, repository: RecommendationRepository):
        self.repository = repository

    def optimize_session(
        self,
        *,
        user_id: int,
        ranked_songs: list[RankedSong],
        limit: int,
    ) -> tuple[list[RankedSong], models.PlaybackSession]:
        """Penalize repeats and recent skips while encouraging genre diversity."""
        session = self.repository.playback.get_or_create_session(user_id)
        recent_events = self.repository.playback.get_recent_user_events(user_id, hours=12, limit=25)
        recent_artists = [event.song.artist for event in recent_events if event.song and event.song.artist]
        recent_genres = [event.song.genre for event in recent_events if event.song and event.song.genre]
        recent_skips = self.repository.playback.recently_skipped_song_ids(user_id, hours=24, limit=25)

        optimized: list[RankedSong] = []
        remaining = ranked_songs[:]
        while remaining and len(optimized) < limit:
            best_index = 0
            best_score = float("-inf")

            for index, ranked in enumerate(remaining):
                adjusted_score, diversity_adjustment, session_penalty = self._session_adjusted_score(
                    ranked=ranked,
                    recent_artists=recent_artists,
                    recent_genres=recent_genres,
                    recent_skips=recent_skips,
                    queued=optimized,
                )
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_index = index
                    remaining[index].score = round(adjusted_score, 4)
                    remaining[index].breakdown.diversity_adjustment = round(diversity_adjustment, 4)
                    remaining[index].breakdown.session_penalty = round(session_penalty, 4)

            chosen = remaining.pop(best_index)
            optimized.append(chosen)
            recent_artists.append(chosen.song.artist)
            recent_genres.append(chosen.song.genre)

        self.repository.playback.replace_session_recommendations(
            session.id,
            [(item.song.navidrome_song_id, item.score) for item in optimized],
        )
        return optimized, session

    def _session_adjusted_score(
        self,
        *,
        ranked: RankedSong,
        recent_artists: list[str],
        recent_genres: list[str],
        recent_skips: set[int],
        queued: list[RankedSong],
    ) -> tuple[float, float, float]:
        """Apply repeat, skip, and diversity adjustments to a ranked song."""
        diversity_adjustment = 0.0
        session_penalty = 0.0

        if ranked.song.id in recent_skips:
            session_penalty -= 18.0

        if recent_artists and ranked.song.artist == recent_artists[-1]:
            session_penalty -= 10.0
        elif ranked.song.artist not in recent_artists[-3:]:
            diversity_adjustment += 4.0

        if recent_genres and ranked.song.genre != recent_genres[-1]:
            diversity_adjustment += 2.5
        elif recent_genres.count(ranked.song.genre) >= 2:
            session_penalty -= 3.0

        if queued and any(item.song.navidrome_song_id == ranked.song.navidrome_song_id for item in queued):
            session_penalty -= 50.0

        return ranked.score + diversity_adjustment + session_penalty, diversity_adjustment, session_penalty


class RecommendationService:
    """Coordinates recommendation generation, caching, and compatibility adapters."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = RecommendationRepository(db)
        self.fast_layer = FastRecommendationLayer(self.repository)
        self.ranking_engine = RankingEngine(self.repository)
        self.session_optimizer = SessionOptimizer(self.repository)
        settings = get_settings()
        self.recommendation_cache = CacheClient(settings.recommendation_cache_ttl_seconds)
        self.trending_cache = CacheClient(settings.trending_cache_ttl_seconds)

    def get_home_recommendations(
        self,
        *,
        user_id: int,
        limit: int = 12,
    ) -> schemas.RecommendationHomeResponse:
        """Return a cached home feed for the authenticated user."""
        self._ensure_user_exists(user_id)
        cache_key = f"recommendations:home:{user_id}:{limit}"
        cached = self.recommendation_cache.get(cache_key)
        if cached is not None:
            return schemas.RecommendationHomeResponse.model_validate(cached)

        candidates = self.fast_layer.get_candidate_songs(user_id=user_id, limit=max(limit * 10, 50))
        ranked = self.ranking_engine.rank_songs(user_id=user_id, candidates=candidates)
        optimized, _session = self.session_optimizer.optimize_session(
            user_id=user_id,
            ranked_songs=ranked,
            limit=limit,
        )
        payload = schemas.RecommendationHomeResponse(
            generated_at=datetime.now(UTC),
            recommendations=[self._serialize_ranked_song(item) for item in optimized],
        )
        self.recommendation_cache.set(cache_key, payload.model_dump(mode="json"))
        return payload

    def get_next_recommendations(
        self,
        *,
        user_id: int,
        song_id: str,
        limit: int = 8,
    ) -> schemas.RecommendationNextResponse:
        """Return the next-song queue anchored on the current track."""
        self._ensure_user_exists(user_id)
        if self.repository.songs.get_by_navidrome_id(song_id) is None:
            raise ValueError("song_not_found")

        candidates = self.fast_layer.get_candidate_songs(
            user_id=user_id,
            current_song_id=song_id,
            limit=max(limit * 10, 50),
        )
        ranked = self.ranking_engine.rank_songs(user_id=user_id, candidates=candidates)
        optimized, _session = self.session_optimizer.optimize_session(
            user_id=user_id,
            ranked_songs=[item for item in ranked if item.song.navidrome_song_id != song_id],
            limit=limit,
        )
        return schemas.RecommendationNextResponse(
            generated_at=datetime.now(UTC),
            current_song_id=song_id,
            recommendations=[self._serialize_ranked_song(item) for item in optimized],
        )

    def get_trending_recommendations(self, *, limit: int = 12) -> schemas.TrendingResponse:
        """Return trending songs from internal playback activity only."""
        cache_key = f"recommendations:trending:{limit}"
        cached = self.trending_cache.get(cache_key)
        if cached is not None:
            return schemas.TrendingResponse.model_validate(cached)

        trending_ids = self.repository.playback.trending_song_ids(limit=max(limit * 4, 20))
        songs = (
            self.db.query(models.LibrarySong)
            .filter(models.LibrarySong.id.in_(trending_ids))
            .all()
            if trending_ids
            else self.repository.songs.list_catalog(limit=limit)
        )
        stats = self.repository.playback.song_event_stats([song.id for song in songs], hours=24 * 7)
        response = schemas.TrendingResponse(
            generated_at=datetime.now(UTC),
            recommendations=[
                schemas.TrendingSongResponse(
                    song_id=song.navidrome_song_id,
                    title=song.title,
                    artist=song.artist,
                    genre=song.genre,
                    stream_url=song.stream_path,
                    play_count=int(stats.get(song.id, {}).get("play_count", song.play_count_7d)),
                    completion_rate=round(float(stats.get(song.id, {}).get("completion_rate", 0.0)), 4),
                    skip_rate=round(float(stats.get(song.id, {}).get("skip_rate", song.skip_rate)), 4),
                    hot_score=round(self._trending_hot_score(song, stats.get(song.id, {})), 4),
                    metadata={"source": "internal-playback"},
                )
                for song in sorted(
                    songs,
                    key=lambda row: self._trending_hot_score(row, stats.get(row.id, {})),
                    reverse=True,
                )[:limit]
            ],
        )
        self.trending_cache.set(cache_key, response.model_dump(mode="json"))
        return response

    def get_personalized_feed(
        self,
        *,
        user_id: int,
        location: str | None = None,
        limit: int,
        target_date: date | None = None,
    ) -> schemas.PersonalizedFeedResponse:
        """Compatibility adapter for older endpoints."""
        response = self.get_home_recommendations(user_id=user_id, limit=limit)
        return schemas.PersonalizedFeedResponse(
            user_id=user_id,
            location=location,
            model_backend="behavioral_recommendation_v2",
            taste_vector=schemas.TasteVectorOut(
                qenet_mode_affinity={},
                genre_affinity={},
                average_tempo=0.0,
                acoustic_signature={},
            ),
            lookalike_audience=[],
            recommendations=response.recommendations,
        )

    def get_hybrid_feed(
        self,
        *,
        location: str | None,
        limit: int,
        target_date: date | None = None,
        user_id: int | None = None,
    ) -> schemas.HybridRecommendationResponse:
        """Compatibility adapter that falls back to trending when no user is provided."""
        if user_id is not None:
            home = self.get_home_recommendations(user_id=user_id, limit=limit)
            recommendations = home.recommendations
        else:
            recommendations = [
                schemas.RecommendationSong(
                    song_id=item.song_id,
                    title=item.title,
                    artist=item.artist,
                    genre=item.genre,
                    stream_url=item.stream_url,
                    score=item.hot_score,
                    reasons=["trending with listeners"],
                    breakdown=schemas.RecommendationBreakdown(
                        completion_rate=item.completion_rate,
                        skip_rate=item.skip_rate,
                        popularity=item.hot_score,
                        recency=0.0,
                        diversity_adjustment=0.0,
                        session_penalty=0.0,
                    ),
                )
                for item in self.get_trending_recommendations(limit=limit).recommendations
            ]
        return schemas.HybridRecommendationResponse(
            date=(target_date or date.today()).isoformat(),
            holiday=None,
            location=location,
            model_backend="behavioral_recommendation_v2",
            recommendations=recommendations,
        )

    def recommend_playlists(self, *, target_date: date | None = None) -> schemas.PlaylistRecommendationResponse:
        """Compatibility response while playlist recommendations are out of scope."""
        return schemas.PlaylistRecommendationResponse(
            date=(target_date or date.today()).isoformat(),
            holiday=None,
            recommendations=[],
        )

    def get_trending_feed(
        self,
        *,
        location: str | None,
        limit: int,
    ) -> schemas.TrendingResponse:
        """Compatibility wrapper for older trending route."""
        return self.get_trending_recommendations(limit=limit)

    def _ensure_user_exists(self, user_id: int) -> None:
        if self.repository.users.get_by_id(user_id) is None:
            raise ValueError("user_not_found")

    def _serialize_ranked_song(self, ranked: RankedSong) -> schemas.RecommendationSong:
        return schemas.RecommendationSong(
            song_id=ranked.song.navidrome_song_id,
            title=ranked.song.title,
            artist=ranked.song.artist,
            genre=ranked.song.genre,
            stream_url=ranked.song.stream_path,
            score=ranked.score,
            reasons=ranked.reasons,
            breakdown=ranked.breakdown,
            source="internal",
            source_metadata={},
        )

    def _trending_hot_score(self, song: models.LibrarySong, stats: dict[str, object]) -> float:
        play_count = float(stats.get("play_count", song.play_count_7d))
        completion_rate = float(stats.get("completion_rate", 0.0))
        skip_rate = float(stats.get("skip_rate", song.skip_rate))
        return play_count * 0.55 + completion_rate * 35.0 + (1.0 - min(skip_rate, 1.0)) * 10.0
