import pytest
from fastapi import status
from app.models.song import LibrarySong
from app.models.user import User
from app.core.security import get_current_user_id
from app.schemas.recommendation import optimize_session

@pytest.fixture
def test_user(db_session):
    user = User(
        email="tester@reco.com",
        device_class="standard",
        is_telegram_user=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_songs(db_session):
    # Create songs with specific genres and play counts to test ranking
    s1 = LibrarySong(
        navidrome_song_id="rec1", title="Pop Song 1", artist="Artist A", 
        genre="Pop", tempo=120.0, duration=200.0, play_count_7d=10
    )
    s2 = LibrarySong(
        navidrome_song_id="rec2", title="Pop Song 2", artist="Artist B", 
        genre="Pop", tempo=125.0, duration=210.0, play_count_7d=50
    )
    s3 = LibrarySong(
        navidrome_song_id="rec3", title="Rock Song 1", artist="Artist C", 
        genre="Rock", tempo=140.0, duration=180.0, play_count_7d=100
    )
    db_session.add_all([s1, s2, s3])
    db_session.commit()
    return [s1, s2, s3]

def test_get_next_song_recommendation(client, test_user, sample_songs):
    """
    Test that the recommendation engine:
    1. Filters by genre (Pop -> Pop)
    2. Ranks by play count (s2 has 50 vs s1 has 10)
    """
    from app.main import app
    
    # Mock authentication to return our test user ID
    app.dependency_overrides[get_current_user_id] = lambda: test_user.id
    
    try:
        # Current song is Pop Song 1
        current_song_id = sample_songs[0].id
        response = client.get(f"/api/v1/recommendations/next?song_id={current_song_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should recommend Pop Song 2 because it's the same genre and has a higher play count
        # Even though Rock Song 1 has the highest overall play count, it's the wrong genre.
        assert data["title"] == "Pop Song 2"
        assert data["artist"] == "Artist B"
        
    finally:
        app.dependency_overrides.clear()

def test_optimize_session_limit():
    """
    Test that optimize_session limits the result to 10 songs even if more are available.
    """
    class MockSong:
        def __init__(self, artist):
            self.artist = artist

    # Create 15 songs with unique artists
    songs = [MockSong(f"Artist {i}") for i in range(15)]
    
    optimized = optimize_session(songs)
    assert len(optimized) == 10
    # Verify we got the first 10 candidates
    assert optimized[0].artist == "Artist 0"
    assert optimized[9].artist == "Artist 9"

def test_optimize_session_unique_artists():
    """
    Test that optimize_session filters out duplicate artists.
    """
    class MockSong:
        def __init__(self, artist):
            self.artist = artist

    songs = [MockSong("Artist A"), MockSong("Artist A"), MockSong("Artist B")]
    
    optimized = optimize_session(songs)
    assert len(optimized) == 2
    assert optimized[0].artist == "Artist A"
    assert optimized[1].artist == "Artist B"