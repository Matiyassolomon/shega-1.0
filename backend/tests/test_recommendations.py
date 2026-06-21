"""
Recommendations API Tests
Tests for recommendation endpoints.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_recommendations_top_feed():
    """Test top songs feed endpoint."""
    response = client.get("/recommendations/feed/top?location=ET&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "top"
    assert data["location"] == "ET"
    assert "songs" in data
    assert isinstance(data["songs"], list)


def test_recommendations_trending_feed():
    """Test trending songs feed endpoint."""
    response = client.get("/recommendations/feed/trending?location=ET&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "trending"
    assert data["location"] == "ET"
    assert "songs" in data
    assert isinstance(data["songs"], list)


def test_recommendations_for_you_feed():
    """Test personalized feed endpoint."""
    response = client.get("/recommendations/feed/for-you?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "for_you"
    assert "user_id" in data
    assert "songs" in data
    assert isinstance(data["songs"], list)


def test_recommendations_friends_feed():
    """Test friends activity feed endpoint."""
    response = client.get("/recommendations/feed/friends?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "friends"
    assert "user_id" in data
    assert "songs" in data
    assert isinstance(data["songs"], list)


def test_recommendations_analytics():
    """Test recommendation analytics endpoint."""
    response = client.get("/recommendations/analytics?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert "total_recommendations_shown" in data
    assert "recommendation_click_rate" in data
    assert "top_genres" in data


def test_recommendations_explain():
    """Test recommendation explainability endpoint."""
    response = client.get("/recommendations/explain?user_id=1&song_id=test-song-1")
    # May return 404 if song doesn't exist, but should not return 500
    assert response.status_code in [200, 404]
