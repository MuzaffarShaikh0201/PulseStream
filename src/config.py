"""
Configuration management for the Event Platform.
All settings loaded from environment variables (e.g. from Bitwarden).
No defaults - all values must be provided.
"""

from typing import Literal
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings - all from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application Settings
    app_name: str = Field(description="Application name")
    app_version: str = Field(description="Application version")
    base_url: str = Field(description="Base URL")
    support_email: str = Field(description="Support email")
    environment: Literal["development", "staging", "production"] = Field(
        description="Application environment"
    )
    debug: bool = Field(description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        description="Logging level"
    )

    # Server Configuration
    host: str = Field(description="Server host")
    port: int = Field(description="Server port")
    workers: int = Field(description="Number of worker processes")

    # PostgreSQL Configuration
    postgres_host: str = Field(description="PostgreSQL host")
    postgres_port: int = Field(description="PostgreSQL port")
    postgres_user: str = Field(description="PostgreSQL user")
    postgres_password: str = Field(description="PostgreSQL password")
    postgres_db: str = Field(description="PostgreSQL database name")
    postgres_pool_size: int = Field(description="PostgreSQL pool size")
    postgres_max_overflow: int = Field(description="PostgreSQL max overflow")

    # Redis Configuration
    redis_host: str = Field(description="Redis host")
    redis_port: int = Field(description="Redis port")
    redis_password: str = Field(description="Redis password (empty if none)")
    redis_db: int = Field(description="Redis database number")
    redis_pool_size: int = Field(description="Redis pool size")

    # Redis Streams Configuration
    redis_stream_user_events: str = Field(description="User events stream key")
    redis_stream_activity_events: str = Field(description="Activity events stream key")
    redis_stream_transaction_events: str = Field(
        description="Transaction events stream key"
    )
    redis_stream_system_events: str = Field(description="System events stream key")
    redis_consumer_group: str = Field(description="Redis consumer group name")
    redis_stream_maxlen: int = Field(description="Redis stream max length")
    redis_batch_size: int = Field(description="Redis batch size")

    # Performance Settings
    event_batch_size: int = Field(description="Event batch size")
    processing_timeout: int = Field(description="Processing timeout in seconds")
    max_retries: int = Field(description="Max retry attempts")

    # Data Retention (in days)
    raw_events_retention_days: int = Field(description="Raw events retention days")
    minute_agg_retention_days: int = Field(description="Minute aggregations retention")
    hourly_agg_retention_days: int = Field(description="Hourly aggregations retention")
    daily_agg_retention_days: int = Field(description="Daily aggregations retention")

    # Authentication
    admin_api_key: str = Field(description="Admin API key")
    user_api_key: str = Field(description="User API key")

    # Rate Limiting
    enable_rate_limiting: bool = Field(description="Enable rate limiting")
    default_rate_limit: str = Field(description="Default rate limit")

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


settings = get_settings()
