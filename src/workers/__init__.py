"""
Worker initialization.
"""

from .aggregator import AggregationWorker
from .base_worker import EventConsumerWorker

__all__ = ["EventConsumerWorker", "AggregationWorker"]
