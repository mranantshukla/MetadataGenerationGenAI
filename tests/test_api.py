# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_api_info():
    """Test API info endpoint."""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "supported_formats" in data


def test_list_documents():
    """Test listing documents."""
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "documents" in data


def test_home_page():
    """Test home page loads."""
    response = client.get("/")
    assert response.status_code == 200

