"""
Pydantic models for miscellaneous routes.
These models are used for API request/response validation.
"""

from typing import Dict
from pydantic import BaseModel, ConfigDict, Field


class Root200Response(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service": "PulseStream",
                "version": "0.1.0",
                "environment": "development",
                "docs": "/docs",
            }
        }
    )

    service: str = Field(description="The name of the service.")
    version: str = Field(description="The version of the service.")
    environment: str = Field(description="The environment the service is running in.")
    docs: str = Field(description="The URL of the documentation.")


class Health200Response(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "service": "PulseStream",
                "version": "0.1.0",
                "environment": "development",
                "dependencies": {
                    "redis": "healthy",
                    "database": "healthy",
                },
            }
        }
    )

    status: str = Field(description="The health status of the application.")
    service: str = Field(description="The name of the service.")
    version: str = Field(description="The version of the service.")
    environment: str = Field(description="The environment the service is running in.")
    dependencies: Dict[str, str] = Field(description="The dependencies of the service.")
