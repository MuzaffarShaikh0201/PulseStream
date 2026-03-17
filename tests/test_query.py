"""
Tests for query routes (GET /events, GET /events/{id}, GET /analytics/realtime).
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.models import RealtimeMetrics


class TestQueryEvents:
    """Tests for GET /events endpoint."""

    def test_query_requires_auth(self, client: TestClient) -> None:
        """Test query events returns 401 without API key."""
        response = client.get("/events")
        assert response.status_code == 401

    def test_query_returns_200_with_auth(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test query events returns 200 with API key."""
        response = client.get("/events", headers=user_headers)
        assert response.status_code == 200

    def test_query_returns_list(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test query events returns a list."""
        response = client.get("/events", headers=user_headers)
        data = response.json()
        assert isinstance(data, list)

    def test_query_supports_limit_param(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test query events respects limit parameter."""
        response = client.get("/events?limit=5", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_query_supports_offset_param(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test query events respects offset parameter."""
        response = client.get("/events?offset=0&limit=10", headers=user_headers)
        assert response.status_code == 200

    def test_query_supports_event_type_filter(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test query events with event_type filter."""
        response = client.get(
            "/events?event_type=activity.page_view", headers=user_headers
        )
        assert response.status_code == 200
        data = response.json()
        for event in data:
            assert event["event_type"] == "activity.page_view"

    def test_query_supports_user_id_filter(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test query events with user_id filter."""
        response = client.get("/events?user_id=user_123", headers=user_headers)
        assert response.status_code == 200


class TestGetEventById:
    """Tests for GET /events/{event_id} endpoint."""

    def test_get_event_requires_auth(self, client: TestClient) -> None:
        """Test get event by ID returns 401 without API key."""
        response = client.get(f"/events/{uuid4()}")
        assert response.status_code == 401

    def test_get_event_returns_404_for_nonexistent(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test get event returns 404 for non-existent event."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/events/{fake_id}", headers=user_headers)
        assert response.status_code == 404

    def test_get_event_returns_422_for_invalid_uuid(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test get event returns 422 for invalid UUID format."""
        response = client.get("/events/not-a-uuid", headers=user_headers)
        assert response.status_code == 422


class TestRealtimeMetrics:
    """Tests for GET /analytics/realtime endpoint."""

    def test_realtime_requires_auth(self, client: TestClient) -> None:
        """Test realtime metrics returns 401 without API key."""
        response = client.get("/analytics/realtime")
        assert response.status_code == 401

    def test_realtime_returns_200_with_auth(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test realtime metrics returns 200 with API key."""
        response = client.get("/analytics/realtime", headers=user_headers)
        assert response.status_code == 200

    def test_realtime_returns_valid_schema(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test realtime metrics response matches RealtimeMetrics schema."""
        response = client.get("/analytics/realtime", headers=user_headers)
        data = response.json()
        RealtimeMetrics.model_validate(data)
        assert "timestamp" in data
        assert "events_per_second" in data
        assert "active_users_1min" in data
        assert "active_users_5min" in data
        assert "active_users_1hour" in data
        assert "top_events" in data
        assert "error_rate" in data
        assert "avg_processing_latency_ms" in data

    def test_realtime_metrics_types(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test realtime metrics has correct value types."""
        response = client.get("/analytics/realtime", headers=user_headers)
        data = response.json()
        assert isinstance(data["events_per_second"], (int, float))
        assert isinstance(data["active_users_1min"], int)
        assert isinstance(data["active_users_5min"], int)
        assert isinstance(data["active_users_1hour"], int)
        assert isinstance(data["top_events"], list)
        assert isinstance(data["error_rate"], (int, float))
        assert isinstance(data["avg_processing_latency_ms"], (int, float))
