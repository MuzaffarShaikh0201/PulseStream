"""
Logging configuration for PulseStream.
"""

import sys
import logging

import coloredlogs
from pythonjsonlogger import json as jsonlogger

from ..config import settings


def setup_logging() -> None:
    """Configure application logging."""

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level))

    # Remove existing handlers
    logger.handlers.clear()

    if settings.is_production:
        # JSON format for production
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        # Colored human-readable format for development
        coloredlogs.install(
            level=getattr(logging, settings.log_level),
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            field_styles=dict(
                name=dict(color="yellow", bold=True, bright=True, italic=True),
                asctime=dict(color="blue", bold=True, bright=True),
                message=dict(color="green", bold=True, bright=True),
                levelname=dict(color="cyan", bold=True, bright=True),
            ),
            level_styles=dict(
                debug=dict(color="white", bold=True, bright=True),
                info=dict(color="green", bold=True, bright=True),
                warning=dict(color="yellow", bold=True, bright=True),
                error=dict(color="magenta", bold=True, bright=True),
                critical=dict(color="red", bold=True, bright=True),
            ),
        )

    # Set specific log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
