"""
FastAPI dependencies for authentication and authorization.
"""

from fastapi import Depends, Header, HTTPException, status

from wfc.servers.rest_api.auth import APIKeyStore
from wfc.shared.config.wfc_config import ProjectContext, WFCConfig


def get_api_key_store() -> APIKeyStore:
    """Get the global APIKeyStore instance (testable singleton via dependency_overrides)."""
    if not hasattr(get_api_key_store, "_instance"):
        get_api_key_store._instance = APIKeyStore()
    return get_api_key_store._instance


async def get_project_context(
    x_project_id: str = Header(..., description="Project ID"),
    authorization: str = Header(..., description="Bearer <api_key>"),
    api_key_store: APIKeyStore = Depends(get_api_key_store),
) -> ProjectContext:
    """
    Dependency to authenticate request and return ProjectContext.

    Args:
        x_project_id: Project ID from X-Project-ID header
        authorization: API key from Authorization header (Bearer <key>)
        api_key_store: Injected APIKeyStore instance

    Returns:
        ProjectContext for authenticated project

    Raises:
        HTTPException: 401 if authentication fails
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <api_key>",
        )

    api_key = authorization[7:]

    if not api_key_store.validate_api_key(x_project_id, api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or project ID",
        )

    developer_id = api_key_store.get_developer_id(x_project_id)
    if not developer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Project not found",
        )

    config = WFCConfig()
    return config.create_project_context(x_project_id, developer_id)
