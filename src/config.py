"""
Configuration management for the Event Platform.
Uses Pydantic Settings for type-safe configuration with environment variable support.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application Settings
    app_name: str = Field(default="PulseStream", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Application environment"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of worker processes")

    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="eventuser", description="PostgreSQL user")
    postgres_password: str = Field(
        default="eventpass", description="PostgreSQL password"
    )
    postgres_db: str = Field(default="eventdb", description="PostgreSQL database name")
    postgres_pool_size: int = Field(
        default=20, description="PostgreSQL connection pool size"
    )
    postgres_max_overflow: int = Field(
        default=10, description="PostgreSQL max overflow connections"
    )

    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: str = Field(default="", description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_pool_size: int = Field(default=10, description="Redis connection pool size")

    # Redis Streams Configuration
    redis_stream_user_events: str = Field(
        default="events:user", description="User events stream key"
    )
    redis_stream_activity_events: str = Field(
        default="events:activity", description="Activity events stream key"
    )
    redis_stream_transaction_events: str = Field(
        default="events:transaction", description="Transaction events stream key"
    )
    redis_stream_system_events: str = Field(
        default="events:system", description="System events stream key"
    )
    redis_consumer_group: str = Field(
        default="event-processors", description="Consumer group name"
    )
    redis_stream_maxlen: int = Field(
        default=100000, description="Maximum stream length"
    )
    redis_batch_size: int = Field(
        default=100, description="Batch size for stream reads"
    )

    # Performance Settings
    event_batch_size: int = Field(
        default=500, description="Batch size for event processing"
    )
    processing_timeout: int = Field(
        default=30, description="Processing timeout in seconds"
    )
    max_retries: int = Field(
        default=3, description="Maximum retry attempts for failed operations"
    )

    # Data Retention (in days)
    raw_events_retention_days: int = Field(
        default=90, description="Raw events retention period"
    )
    minute_agg_retention_days: int = Field(
        default=7, description="Minute aggregations retention period"
    )
    hourly_agg_retention_days: int = Field(
        default=90, description="Hourly aggregations retention period"
    )
    daily_agg_retention_days: int = Field(
        default=730, description="Daily aggregations retention period"
    )

    # Authentication
    admin_api_key: str = Field(
        default="", description="Admin API key (leave empty to auto-generate)"
    )
    require_api_key: bool = Field(
        default=False, description="Require API key for all endpoints"
    )

    # Rate Limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    default_rate_limit: str = Field(
        default="100/minute", description="Default rate limit"
    )

    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_url_sync(self) -> str:
        """Generate synchronous PostgreSQL connection URL (for Alembic)."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL."""
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:"
                f"{self.redis_port}/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    def get_stream_key(self, event_type: str) -> str:
        """
        Get the appropriate Redis stream key for an event type.

        Args:
            event_type: Event type (e.g., 'user.login', 'activity.click')

        Returns:
            Redis stream key
        """
        event_category = event_type.split(".")[0]
        stream_mapping = {
            "user": self.redis_stream_user_events,
            "activity": self.redis_stream_activity_events,
            "transaction": self.redis_stream_transaction_events,
            "system": self.redis_stream_system_events,
        }
        return stream_mapping.get(event_category, self.redis_stream_system_events)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings instance
    """
    return Settings()


# Export settings instance
settings = get_settings()
