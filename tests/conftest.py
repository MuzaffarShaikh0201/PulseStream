"""
Pytest configuration and shared fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client. Uses context manager so lifespan (Redis/DB init) runs."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def admin_headers(client: TestClient) -> dict:
    """Admin API key headers. Depends on client so lifespan runs first."""
    from src.config import settings

    return {"X-API-Key": settings.admin_api_key}


@pytest.fixture
def user_headers(client: TestClient) -> dict:
    """User API key headers. Depends on client so lifespan runs first."""
    from src.config import settings

    return {"X-API-Key": settings.user_api_key}
