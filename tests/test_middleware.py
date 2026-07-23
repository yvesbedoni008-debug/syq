"""Tests for security middleware"""

import pytest
from unittest.mock import Mock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.middleware.security import SecurityHeadersMiddleware, RateLimitMiddleware
from app.middleware.logging import LoggingMiddleware


def test_security_headers_middleware():
    """Test that security headers are added"""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.get("/test")

    # Check that security headers are present
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"] == "geolocation=(), microphone=(), camera=()"
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_rate_limit_middleware():
    """Test rate limiting functionality"""
    app = FastAPI()
    # Set low limit for testing: 2 requests per 5 seconds
    app.add_middleware(RateLimitMiddleware, calls=2, period=5)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)

    # First request should succeed
    response1 = client.get("/test")
    assert response1.status_code == 200

    # Second request should succeed
    response2 = client.get("/test")
    assert response2.status_code == 200

    # Third request should be rate limited
    response3 = client.get("/test")
    assert response3.status_code == 429
    assert "Rate limit exceeded" in response3.json()["detail"]


def test_logging_middleware_adds_request_id():
    """Test that logging middleware adds request ID to request state"""
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        # Check that request ID was added
        assert hasattr(request.state, "request_id")
        assert request.state.request_id is not None
        return {"message": "test"}

    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])