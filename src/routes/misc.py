"""
Miscellaneous routes for the PulseStream API.
"""

from fastapi.responses import JSONResponse
from fastapi import APIRouter, Request, status

from ..config import settings
from ..utils.logging import get_logger
from ..schemas.misc import HEALTH_RESPONSE_MODEL, ROOT_RESPONSE_MODEL


logger = get_logger(__name__)
router = APIRouter(tags=["Misc"])


@router.get(
    path="/",
    summary="Root endpoint",
    description="Root endpoint for the PulseStream API.",
    responses=ROOT_RESPONSE_MODEL,
)
async def root(request: Request):
    """
    Root endpoint with API information.

    # Args:
    - request: Request - The request object.

    # Returns:
    - JSONResponse: A JSON response containing the service information.
        - status_code: The status code of the response.
        - content: A dictionary containing the service information.
            - service: The name of the service.
            - version: The version of the service.
            - environment: The environment the service is running in.
            - docs: The URL of the documentation.
    """

    logger.info("GET / - Root endpoint called")
    logger.info("GET / - Response: 200 OK - Root endpoint completed successfully")

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "docs": "/docs" if settings.is_development else "disabled",
        },
    )


@router.get(
    path="/health",
    summary="Health check endpoint",
    description="Health check endpoint for the PulseStream API.",
    responses=HEALTH_RESPONSE_MODEL,
)
async def health(request: Request):
    """
    Health check endpoint.

    # Args:
    - request: Request - The request object.

    # Returns:
    - JSONResponse: A JSON response containing the health status.
        - status_code: The status code of the response.
        - content: A dictionary containing the health status.
            - status: The health status of the application.
            - service: The name of the service.
            - version: The version of the service.
            - environment: The environment the service is running in.
            - docs: The URL of the documentation.
    """

    logger.info("GET /health - Health check endpoint called")

    # Check Redis connection
    # TODO: Check Redis connection

    # Check database connection (simple query)
    # TODO: Check database connection

    logger.info(
        "GET /health - Response: 200 OK - Health check endpoint completed successfully"
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
    )
