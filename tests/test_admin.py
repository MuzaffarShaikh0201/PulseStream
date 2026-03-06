"""
Tests for admin routes (/stats, /streams).
"""

import pytest
from fastapi.testclient import TestClient

from src.config import settings
from src.models import StreamStatsResponse, SystemStatsResponse


class TestAdminStatsEndpoint:
    """Tests for GET /stats endpoint."""

    def test_stats_requires_auth(self, client: TestClient) -> None:
        """Test stats endpoint returns 401 without API key."""
        response = client.get("/stats")
        assert response.status_code == 401

    def test_stats_rejects_user_key(self, client: TestClient, user_headers: dict) -> None:
        """Test stats endpoint returns 403 with user key (requires admin)."""
        response = client.get("/stats", headers=user_headers)
        assert response.status_code == 403

    def test_stats_returns_200_with_admin_key(
        self, client: TestClient, admin_headers: dict
    ) -> None:
        """Test stats endpoint returns 200 with admin API key."""
        response = client.get("/stats", headers=admin_headers)
        assert response.status_code == 200

    def test_stats_returns_valid_schema(
        self, client: TestClient, admin_headers: dict
    ) -> None:
        """Test stats response matches SystemStatsResponse schema."""
        response = client.get("/stats", headers=admin_headers)
        data = response.json()
        SystemStatsResponse.model_validate(data)
        assert "total_events" in data
        assert "total_users" in data
        assert "events_by_type" in data
        assert "streams" in data
        assert "aggregations_1min_count" in data
        assert "aggregations_hourly_count" in data
        assert "aggregations_daily_count" in data

    def test_stats_streams_structure(
        self, client: TestClient, admin_headers: dict
    ) -> None:
        """Test stats streams field has expected structure."""
        response = client.get("/stats", headers=admin_headers)
        data = response.json()
        streams = data["streams"]
        StreamStatsResponse.model_validate(streams)
        assert streams["total_streams"] == 4  # user, activity, transaction, system
        assert "streams" in streams
        assert len(streams["streams"]) == 4


class TestAdminStreamsEndpoint:
    """Tests for GET /streams endpoint."""

    def test_streams_requires_auth(self, client: TestClient) -> None:
        """Test streams endpoint returns 401 without API key."""
        response = client.get("/streams")
        assert response.status_code == 401

    def test_streams_rejects_user_key(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test streams endpoint returns 403 with user key."""
        response = client.get("/streams", headers=user_headers)
        assert response.status_code == 403

    def test_streams_returns_200_with_admin_key(
        self, client: TestClient, admin_headers: dict
    ) -> None:
        """Test streams endpoint returns 200 with admin API key."""
        response = client.get("/streams", headers=admin_headers)
        assert response.status_code == 200

    def test_streams_returns_valid_schema(
        self, client: TestClient, admin_headers: dict
    ) -> None:
        """Test streams response matches StreamStatsResponse schema."""
        response = client.get("/streams", headers=admin_headers)
        data = response.json()
        StreamStatsResponse.model_validate(data)
        assert "total_streams" in data
        assert "total_messages" in data
        assert "streams" in data
        for stream in data["streams"]:
            assert "stream_key" in stream
            assert stream["stream_key"] in (
                settings.redis_stream_user_events,
                settings.redis_stream_activity_events,
                settings.redis_stream_transaction_events,
                settings.redis_stream_system_events,
            )
