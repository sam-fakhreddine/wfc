"""Knowledge API authentication dependencies."""

import logging
import os
from typing import Optional

from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)

_KNOWLEDGE_TOKEN: Optional[str] = None


def _get_knowledge_token() -> str:
    """Get the knowledge API token from environment."""
    global _KNOWLEDGE_TOKEN
    if _KNOWLEDGE_TOKEN is None:
        _KNOWLEDGE_TOKEN = os.environ.get("WFC_KNOWLEDGE_TOKEN", "")
    return _KNOWLEDGE_TOKEN


def reset_knowledge_token() -> None:
    """Reset cached token (for testing)."""
    global _KNOWLEDGE_TOKEN
    _KNOWLEDGE_TOKEN = None


async def verify_knowledge_token(
    authorization: str = Header(default=""),
) -> bool:
    """Verify Bearer token for knowledge API endpoints.

    Returns True if valid, raises 401 if invalid.
    """
    token = _get_knowledge_token()
    if not token:
        return True

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    provided = authorization[7:]
    if provided != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    return True


async def optional_knowledge_token(
    authorization: str = Header(default=""),
) -> bool:
    """Optional auth check -- returns True if valid, False if missing/invalid. Never raises."""
    token = _get_knowledge_token()
    if not token:
        return True
    if not authorization.startswith("Bearer "):
        return False
    return authorization[7:] == token
