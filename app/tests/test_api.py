"""Unit tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.server.main import app

client = TestClient(app)


def test_healthz():
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_solving_invalid_secret():
    """Test that invalid secret returns 403."""
    response = client.post(
        "/solving",
        json={
            "email": "test@example.com",
            "secret": "wrong",
            "url": "http://example.com/quiz"
        }
    )
    assert response.status_code == 403


def test_solving_missing_fields():
    """Test that missing fields return 422."""
    response = client.post("/solving", json={"email": "test@example.com"})
    assert response.status_code == 422


def test_solving_invalid_url():
    """Test that invalid URL returns 422."""
    response = client.post(
        "/solving",
        json={
            "email": "test@example.com",
            "secret": "changeme",
            "url": "not-a-url"
        }
    )
    assert response.status_code == 422
