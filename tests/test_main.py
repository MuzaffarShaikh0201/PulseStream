"""
Tests for FastAPI application (docs, OpenAPI).
"""

from fastapi.testclient import TestClient


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
