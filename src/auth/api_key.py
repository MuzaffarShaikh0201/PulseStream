"""
API Key authentication.
"""

import secrets
from typing import Optional

from fastapi.security import APIKeyHeader
from fastapi import HTTPException, Security, status

from ..config import settings


# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyManager:
    """
    Manages API keys for authentication.
    In production, store these in a database.
    """

    def __init__(self):
        # In production, load from database
        # For now, use environment variable or generate default keys
        self._api_keys = self._load_api_keys()

    def _load_api_keys(self) -> dict[str, dict]:
        """
        Load API keys from configuration (must be set via env/Bitwarden).

        Returns:
            Dictionary of api_key -> metadata
        """
        admin_key = settings.admin_api_key
        user_key = settings.user_api_key

        return {
            admin_key: {
                "name": "Admin",
                "permissions": ["read", "write", "admin"],
            },
            user_key: {
                "name": "User",
                "permissions": ["read", "write"],
            },
        }

    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a secure random API key.

        Returns:
            API key string
        """
        return f"ps_{secrets.token_urlsafe(32)}"

    def validate_key(self, api_key: str) -> Optional[dict]:
        """
        Validate an API key.

        Args:
            api_key: API key to validate

        Returns:
            API key metadata if valid, None otherwise
        """
        return self._api_keys.get(api_key)

    def has_permission(self, api_key: str, permission: str) -> bool:
        """
        Check if an API key has a specific permission.

        Args:
            api_key: API key
            permission: Permission to check

        Returns:
            True if key has permission, False otherwise
        """
        key_data = self.validate_key(api_key)
        if not key_data:
            return False

        return permission in key_data.get("permissions", [])


# Global API key manager
api_key_manager = APIKeyManager()


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Dependency to validate API key from header.

    Args:
        api_key: API key from header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not api_key_manager.validate_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


async def get_api_key_optional(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """
    Optional API key dependency (for endpoints that work with or without auth).

    Args:
        api_key: API key from header

    Returns:
        Validated API key or None
    """
    if not api_key:
        return None

    if not api_key_manager.validate_key(api_key):
        return None

    return api_key


async def require_admin(api_key: str = Security(get_api_key)) -> str:
    """
    Dependency to require admin permissions.

    Args:
        api_key: Validated API key

    Returns:
        API key

    Raises:
        HTTPException: If not admin
    """
    if not api_key_manager.has_permission(api_key, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required"
        )

    return api_key
