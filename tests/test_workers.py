"""
Tests for workers (AggregationWorker, EventConsumerWorker).
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.workers.aggregator import AggregationWorker
from src.workers.base_worker import EventConsumerWorker


class TestEventConsumerWorkerDeserialize:
    """Tests for EventConsumerWorker._deserialize_event."""

    def test_deserialize_event_valid(self) -> None:
        """Test deserializing a valid event from Redis format."""
        worker = EventConsumerWorker(consumer_name="test-consumer")
        event_data = {
            "event_id": str(uuid4()),
            "event_type": "activity.page_view",
            "user_id": "user_123",
            "session_id": "session_456",
            "timestamp": "2024-01-15T10:30:00+00:00",
            "metadata": "{}",
            "properties": "{}",
            "created_at": "2024-01-15T10:30:00+00:00",
        }
        result = worker._deserialize_event(event_data)
        assert result["event_type"] == "activity.page_view"
        assert result["user_id"] == "user_123"
        assert result["session_id"] == "session_456"
        assert "event_id" in result
        assert "timestamp" in result
        assert "event_metadata" in result
        assert "properties" in result
        assert "created_at" in result

    def test_deserialize_event_empty_user_id(self) -> None:
        """Test deserializing event with empty user_id."""
        worker = EventConsumerWorker(consumer_name="test-consumer")
        event_data = {
            "event_id": str(uuid4()),
            "event_type": "system.error",
            "user_id": "",
            "session_id": "",
            "timestamp": "2024-01-15T10:30:00+00:00",
            "metadata": "{}",
            "properties": "{}",
            "created_at": "2024-01-15T10:30:00+00:00",
        }
        result = worker._deserialize_event(event_data)
        assert result["user_id"] is None
        assert result["session_id"] is None

    def test_deserialize_event_with_metadata(self) -> None:
        """Test deserializing event with metadata and properties."""
        worker = EventConsumerWorker(consumer_name="test-consumer")
        event_data = {
            "event_id": str(uuid4()),
            "event_type": "activity.click",
            "user_id": "user_1",
            "session_id": "sess_1",
            "timestamp": "2024-01-15T10:30:00+00:00",
            "metadata": '{"ip_address": "1.2.3.4"}',
            "properties": '{"button": "submit"}',
            "created_at": "2024-01-15T10:30:00+00:00",
        }
        result = worker._deserialize_event(event_data)
        assert result["event_metadata"] == {"ip_address": "1.2.3.4"}
        assert result["properties"] == {"button": "submit"}


class TestEventConsumerWorkerInit:
    """Tests for EventConsumerWorker initialization."""

    def test_worker_has_consumer_name(self) -> None:
        """Test worker accepts custom consumer name."""
        worker = EventConsumerWorker(consumer_name="my-consumer")
        assert worker.consumer_name == "my-consumer"

    def test_worker_default_consumer_name(self) -> None:
        """Test worker generates default consumer name (hostname-pid format)."""
        worker = EventConsumerWorker()
        assert worker.consumer_name is not None
        assert "-" in worker.consumer_name

    def test_worker_has_streams_config(self) -> None:
        """Test worker has streams configuration."""
        worker = EventConsumerWorker()
        assert len(worker.streams) == 4
        assert all(v == ">" for v in worker.streams.values())

    def test_worker_initial_state(self) -> None:
        """Test worker initial state."""
        worker = EventConsumerWorker()
        assert worker.running is False
        assert worker.processed_count == 0
        assert worker.error_count == 0


class TestAggregationWorkerInit:
    """Tests for AggregationWorker initialization."""

    def test_worker_initial_state(self) -> None:
        """Test aggregation worker initial state."""
        worker = AggregationWorker()
        assert worker.running is False

    @pytest.mark.asyncio
    async def test_stop_sets_running_false(self) -> None:
        """Test stop method sets running to False."""
        worker = AggregationWorker()
        worker.running = True
        await worker.stop()
        assert worker.running is False


@pytest.mark.asyncio
class TestAggregationWorkerRun:
    """Async tests for AggregationWorker.run_aggregations."""

    async def test_run_aggregations_calls_all_aggregators(self) -> None:
        """Test run_aggregations calls 1min, hourly, and daily aggregators."""
        worker = AggregationWorker()
        with (
            patch.object(worker, "_aggregate_one_minute", new_callable=AsyncMock) as mock_1min,
            patch.object(worker, "_aggregate_hourly", new_callable=AsyncMock) as mock_hourly,
            patch.object(worker, "_aggregate_daily", new_callable=AsyncMock) as mock_daily,
        ):
            await worker.run_aggregations()
            mock_1min.assert_called_once()
            mock_hourly.assert_called_once()
            mock_daily.assert_called_once()

    async def test_run_aggregations_handles_exception(self) -> None:
        """Test run_aggregations handles exceptions gracefully."""
        worker = AggregationWorker()
        with patch.object(
            worker, "_aggregate_one_minute", new_callable=AsyncMock, side_effect=Exception("DB error")
        ):
            # Should not raise - exceptions are caught and logged
            await worker.run_aggregations()
