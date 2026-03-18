"""
PostgreSQL database connection and session management.
Uses async SQLAlchemy with asyncpg driver.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import settings


class DatabaseManager:
    """Database connection manager."""

    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def init(self) -> None:
        """Initialize database engine and session factory."""
        self._engine = create_async_engine(
            settings.postgres_url,
            echo=settings.debug,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provide a transactional scope for database operations.

        Usage:
            async with db_manager.session() as session:
                result = await session.execute(query)
                await session.commit()
        """
        if self._session_factory is None:
            raise RuntimeError("DatabaseManager not initialized. Call init() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def get_session(self) -> AsyncSession:
        """
        Get a new database session.
        Caller is responsible for closing the session.
        """
        if self._session_factory is None:
            raise RuntimeError("DatabaseManager not initialized. Call init() first.")

        return self._session_factory()

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        if self._engine is None:
            raise RuntimeError("DatabaseManager not initialized. Call init() first.")
        return self._engine


db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints to get database session.

    Usage in FastAPI:
        @app.get("/events")
        async def get_events(db: AsyncSession = Depends(get_db)):
            result = await db.execute(query)
            return result.scalars().all()
    """
    async with db_manager.session() as session:
        yield session
