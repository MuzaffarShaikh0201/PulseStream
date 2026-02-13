"""
Tests for FastAPI application endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """Test health check returns 200 status."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client: TestClient) -> None:
        """Test health check returns healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "PulseStream"
        assert "version" in data
        assert data["environment"] in ("development", "staging", "production")


class TestRootEndpoint:
    """Tests for / root endpoint."""

    def test_root_returns_200(self, client: TestClient) -> None:
        """Test root endpoint returns 200 status."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_service_info(self, client: TestClient) -> None:
        """Test root endpoint returns service information."""
        response = client.get("/")
        data = response.json()
        assert data["service"] == "PulseStream"
        assert "version" in data
        assert data["environment"] in ("development", "staging", "production")
        assert "docs" in data


class TestOpenAPIDocs:
    """Tests for API documentation endpoints."""

    def test_docs_returns_200(self, client: TestClient) -> None:
        """Test /docs returns 200 when in development."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_docs_returns_swagger_ui(self, client: TestClient) -> None:
        """Test /docs returns Swagger UI HTML."""
        response = client.get("/docs")
        assert "swagger" in response.text.lower()

    def test_redoc_returns_200(self, client: TestClient) -> None:
        """Test /redoc returns 200 when in development."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_redoc_returns_redoc_ui(self, client: TestClient) -> None:
        """Test /redoc returns ReDoc HTML."""
        response = client.get("/redoc")
        assert "redoc" in response.text.lower()
