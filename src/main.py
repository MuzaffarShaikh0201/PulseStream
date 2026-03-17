"""
PulseStream - Main FastAPI application.
High-performance event ingestion and processing platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import db_manager, redis_manager
from .auth.api_key import api_key_manager
from .utils.logging import setup_logging, get_logger
from .custom_openapi import create_custom_openapi_generator
from .routes import misc_router, ingestion_router, admin_router, query_router


# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting PulseStream...")

    # Initialize database connection
    logger.info("Initializing PostgreSQL connection...")
    db_manager.init()

    # Initialize Redis connection
    logger.info("Initializing Redis connection...")
    await redis_manager.init()

    # Verify connections
    redis_connected = await redis_manager.ping()
    if redis_connected:
        logger.info("✓ Redis connection successful")
    else:
        logger.error("✗ Redis connection failed")

    logger.info("✓ API keys configured (from environment)")

    logger.info(
        f"✓ PulseStream started successfully on {settings.environment} environment"
    )

    yield

    # Shutdown
    logger.info("Shutting down PulseStream...")

    # Close Redis connection
    await redis_manager.close()
    logger.info("✓ Redis connection closed")

    # Close database connection
    await db_manager.close()
    logger.info("✓ PostgreSQL connection closed")

    logger.info("✓ PulseStream shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "High-performance, event-driven backend platform for ingesting, processing, "
        "and analyzing large-scale event data in real-time."
    ),
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add custom OpenAPI generator
doc_tags_metadata = [
    {
        "name": "Miscellaneous APIs",
        "description": "Miscellaneous APIs like health check, root, etc. that are not related to any specific functionality.",
    },
]

app.openapi = create_custom_openapi_generator(
    app=app,
    env_config=settings,
    docs_summary="PulseStream API Documentation",
    docs_description=(
        "High-performance, event-driven backend platform for ingesting, processing, "
        "and analyzing large-scale event data in real-time."
    ),
    docs_tags_metadata=doc_tags_metadata,
)


# Include routers
app.include_router(misc_router)
app.include_router(ingestion_router)
app.include_router(query_router)
app.include_router(admin_router)
