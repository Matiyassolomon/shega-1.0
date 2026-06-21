"""
Health Endpoint Tests
Tests for health check endpoints.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_basic():
    """Test basic health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_health_live():
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_health_ready():
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "not_ready"]
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]


def test_health_detailed():
    """Test detailed health check endpoint."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "checks" in data


def test_health_metrics():
    """Test metrics endpoint."""
    response = client.get("/health/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "counters" in data
    assert "gauges" in data
    assert "histograms" in data
