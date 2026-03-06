"""
Routes initialization.
"""

from .misc import router as misc_router
from .ingestion import router as ingestion_router
from .query import router as query_router
from .admin import router as admin_router


__all__ = ["misc_router", "ingestion_router", "query_router", "admin_router"]
