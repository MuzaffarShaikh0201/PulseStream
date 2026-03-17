"""
Tests for ingestion routes (POST /events, POST /events/batch).
"""

import pytest
from fastapi.testclient import TestClient

from src.models import EventBatchResponse, EventResponse


def _valid_event_payload() -> dict:
    """Minimal valid event payload."""
    return {
        "event_type": "activity.page_view",
        "user_id": "user_123",
        "session_id": "session_456",
        "properties": {"page_url": "/test", "page_title": "Test Page"},
    }


class TestIngestSingleEvent:
    """Tests for POST /events endpoint."""

    def test_ingest_requires_auth(self, client: TestClient) -> None:
        """Test ingest endpoint returns 401 without API key."""
        response = client.post("/events", json=_valid_event_payload())
        assert response.status_code == 401

    def test_ingest_returns_202_with_valid_event(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test ingest returns 202 with valid event and API key."""
        response = client.post(
            "/events", json=_valid_event_payload(), headers=user_headers
        )
        assert response.status_code == 202

    def test_ingest_returns_valid_schema(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test ingest response matches EventResponse schema."""
        response = client.post(
            "/events", json=_valid_event_payload(), headers=user_headers
        )
        data = response.json()
        EventResponse.model_validate(data)
        assert data["status"] == "accepted"
        assert "event_id" in data
        assert "timestamp" in data

    def test_ingest_rejects_invalid_event_type(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test ingest rejects invalid event type format."""
        payload = {
            **_valid_event_payload(),
            "event_type": "invalid",
        }
        response = client.post("/events", json=payload, headers=user_headers)
        assert response.status_code == 422

    def test_ingest_rejects_invalid_category(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test ingest rejects invalid event category."""
        payload = {
            **_valid_event_payload(),
            "event_type": "invalid.action",
        }
        response = client.post("/events", json=payload, headers=user_headers)
        assert response.status_code == 422

    def test_ingest_accepts_user_event(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test ingest accepts user.login event."""
        payload = {
            "event_type": "user.login",
            "user_id": "user_789",
            "properties": {"login_method": "password", "success": True},
        }
        response = client.post("/events", json=payload, headers=user_headers)
        assert response.status_code == 202

    def test_ingest_accepts_system_event(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test ingest accepts system.error event."""
        payload = {
            "event_type": "system.error",
            "properties": {
                "error_message": "Test error",
                "error_code": "TEST_ERR",
                "stack_trace": "trace",
            },
        }
        response = client.post("/events", json=payload, headers=user_headers)
        assert response.status_code == 202


class TestIngestBatchEvents:
    """Tests for POST /events/batch endpoint."""

    def test_batch_requires_auth(self, client: TestClient) -> None:
        """Test batch ingest returns 401 without API key."""
        payload = {"events": [_valid_event_payload()]}
        response = client.post("/events/batch", json=payload)
        assert response.status_code == 401

    def test_batch_returns_202_with_valid_events(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test batch ingest returns 202 with valid events."""
        payload = {
            "events": [
                _valid_event_payload(),
                {**_valid_event_payload(), "event_type": "activity.click"},
            ]
        }
        response = client.post(
            "/events/batch", json=payload, headers=user_headers
        )
        assert response.status_code == 202

    def test_batch_returns_valid_schema(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test batch response matches EventBatchResponse schema."""
        payload = {"events": [_valid_event_payload()]}
        response = client.post(
            "/events/batch", json=payload, headers=user_headers
        )
        data = response.json()
        EventBatchResponse.model_validate(data)
        assert data["accepted"] == 1
        assert data["rejected"] == 0
        assert len(data["event_ids"]) == 1

    def test_batch_rejects_empty_events(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test batch ingest rejects empty events list."""
        payload = {"events": []}
        response = client.post(
            "/events/batch", json=payload, headers=user_headers
        )
        assert response.status_code == 422

    def test_batch_multiple_events(
        self, client: TestClient, user_headers: dict
    ) -> None:
        """Test batch ingest with multiple events."""
        payload = {
            "events": [
                {**_valid_event_payload(), "event_type": "user.login", "user_id": "u1"},
                {**_valid_event_payload(), "event_type": "activity.search", "user_id": "u2"},
                {**_valid_event_payload(), "event_type": "transaction.created", "user_id": "u3", "properties": {"transaction_id": "tx1", "amount": 10, "currency": "USD"}},
            ]
        }
        response = client.post(
            "/events/batch", json=payload, headers=user_headers
        )
        assert response.status_code == 202
        data = response.json()
        assert data["accepted"] == 3
        assert len(data["event_ids"]) == 3
