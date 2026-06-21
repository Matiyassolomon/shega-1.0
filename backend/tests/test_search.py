"""
Search API Tests
Tests for search endpoints.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_search_autocomplete():
    """Test search autocomplete endpoint."""
    response = client.get("/search/autocomplete?query=test&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


def test_search_autocomplete_short_query():
    """Test autocomplete with short query (should return empty)."""
    response = client.get("/search/autocomplete?query=t&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) == 0


def test_search_songs():
    """Test song search endpoint."""
    response = client.get("/search/songs?query=test&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test"
    assert "total" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_search_songs_with_sort():
    """Test song search with different sort options."""
    for sort_by in ["relevance", "popularity", "recent"]:
        response = client.get(f"/search/songs?query=test&limit=10&sort_by={sort_by}")
        assert response.status_code == 200
        data = response.json()
        assert data["sort_by"] == sort_by


def test_search_artists():
    """Test artist search endpoint."""
    response = client.get("/search/artists?query=test&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test"
    assert "results" in data
    assert isinstance(data["results"], list)


def test_search_songs_pagination():
    """Test song search pagination."""
    response = client.get("/search/songs?query=test&limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert data["offset"] == 0
