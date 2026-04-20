from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from app.models.song import LibrarySong
from app.models.playback import get_user_recent_events

class RecommendationSong(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    navidrome_song_id: str
    title: str
    artist: str
    genre: str
    cover_art_path: Optional[str] = None

class RecommendationNextResponse(RecommendationSong):
    pass

class RecommendationBreakdown(BaseModel):
    reason: str
    score: float

class RecommendationHomeResponse(BaseModel):
    sections: List[dict]

class TrendingSongResponse(RecommendationSong):
    play_count_7d: int

class TrendingResponse(BaseModel):
    songs: List[TrendingSongResponse]

# 🔵 Layer 1: Candidate Generation
def get_candidate_songs(db: Session, current_song_id: int):
    current_song = db.query(LibrarySong).filter(LibrarySong.id == current_song_id).first()

    if not current_song:
        return []

    candidates = (
        db.query(LibrarySong)
        .filter(LibrarySong.genre == current_song.genre)
        .limit(100)
        .all()
    )

    return candidates


# 🟡 Layer 2: Ranking
def rank_songs(db: Session, user_id: int, songs):
    events = get_user_recent_events(db, user_id)

    skip_songs = {str(e.song_id) for e in events if e.event_type == "skip"}

    ranked = []
    for song in songs:
        score = 0

        if str(song.id) not in skip_songs and song.navidrome_song_id not in skip_songs:
            score += 10

        if song.play_count_7d:
            score += song.play_count_7d * 0.1

        ranked.append((song, score))

    ranked.sort(key=lambda x: x[1], reverse=True)

    return [s[0] for s in ranked]


# 🔴 Layer 3: Session Optimization
def optimize_session(songs):
    seen_artists = set()
    final = []

    for song in songs:
        if song.artist not in seen_artists:
            final.append(song)
            seen_artists.add(song.artist)

        if len(final) >= 10:
            break

    return final


# 🎯 Main function
def get_next_song(db: Session, user_id: int, current_song_id: int):
    candidates = get_candidate_songs(db, current_song_id)
    ranked = rank_songs(db, user_id, candidates)
    optimized = optimize_session(ranked)

    return optimized[0] if optimized else None