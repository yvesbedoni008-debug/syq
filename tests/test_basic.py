"""
Basic test to verify the application structure
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "SYQ" in data["message"]


def test_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_api_v1_root():
    """Test the API v1 root endpoint"""
    response = client.get("/api/v1/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "SYQ API v1" in data["message"]


if __name__ == "__main__":
    test_root_endpoint()
    test_health_endpoint()
    test_api_v1_root()
    print("All basic tests passed!")