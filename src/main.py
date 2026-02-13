"""
PulseStream - Main FastAPI application.
High-performance event ingestion and processing platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import misc_router
from .utils.logging import setup_logging, get_logger
from .custom_openapi import create_custom_openapi_generator


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
    # TODO: Initialize PostgreSQL connection
    # logger.info("Initializing PostgreSQL connection...")

    # Initialize Redis connection
    # TODO: Initialize Redis connection
    # logger.info("Initializing Redis connection...")

    # Log API keys info
    # TODO: Log API keys info

    logger.info(
        f"✓ PulseStream started successfully on {settings.environment} environment"
    )

    yield

    # Shutdown
    logger.info("Shutting down PulseStream...")

    # Close Redis connection
    # TODO: Close Redis connection
    # logger.info("✓ Redis connection closed")

    # Close database connection
    # TODO: Close PostgreSQL connection
    # logger.info("✓ PostgreSQL connection closed")

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
        "name": "Misc",
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
