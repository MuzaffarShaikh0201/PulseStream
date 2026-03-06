"""
Authentication module.
"""

from .api_key import (
    api_key_manager,
    get_api_key,
    get_api_key_optional,
    require_admin,
)

__all__ = [
    "api_key_manager",
    "get_api_key",
    "get_api_key_optional",
    "require_admin",
]
