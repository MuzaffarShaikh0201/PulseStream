"""
PulseStream - Main FastAPI application.
High-performance event ingestion and processing platform.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .utils.logging import setup_logging


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


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
    logger.info("✓ PostgreSQL connection closed")

    logger.info("✓ PulseStream shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="High-performance event ingestion and processing platform",
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


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check(request: Request):
    """
    Health check endpoint.
    Returns the health status of the application and its dependencies.
    """

    logger.info("Health check endpoint called")

    # Check Redis connection
    # TODO: Check Redis connection

    # Check database connection (simple query)
    # TODO: Check database connection

    logger.info("Health check endpoint completed")

    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
    )


@app.get("/", tags=["Root"])
async def root(request: Request):
    """Root endpoint with API information."""

    logger.info("Root endpoint called")
    logger.info("Root endpoint completed")

    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs" if settings.is_development else "disabled",
    }


# Import and include routers
