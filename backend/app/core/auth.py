"""Authentication middleware.

Local-only demo mode: validates a shared-secret API key from the
LOCAL_API_KEY environment variable. Production mode requires OIDC/OIDC
discovery (future milestone).

This module provides a FastAPI dependency that returns the current user
role. The role is "analyst" in local mode (single-key auth).
"""
from __future__ import annotations

from collections import namedtuple
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings, get_settings

# Use auto_error=False so we can return 401 (not 403) for missing credentials
bearer_scheme = HTTPBearer(auto_error=False)

# Role constants for authorization
ROLE_VIEWER = "viewer"
ROLE_ANALYST = "analyst"
ROLE_OPERATOR = "operator"
ROLE_ADMIN = "admin"

_ALL_ROLES = {ROLE_VIEWER, ROLE_ANALYST, ROLE_OPERATOR, ROLE_ADMIN}
_ADMIN_USERS = {"admin"}

UserContext = namedtuple("UserContext", ["role", "user_id", "auth_mode"])


def _role_requires_min(role: str, min_role: str) -> bool:
    """Check if role meets or exceeds the minimum required role."""
    hierarchy = [ROLE_VIEWER, ROLE_ANALYST, ROLE_OPERATOR, ROLE_ADMIN]
    idx = {r: i for i, r in enumerate(hierarchy)}
    return idx.get(role, -1) >= idx.get(min_role, 0)


def _local_mode_rejection() -> HTTPException:
    """Standard 401 for missing/invalid credentials in local mode."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
        detail="Invalid or missing API key",
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> UserContext:
    """Validate the current request's authentication.

    In local mode: checks the API key against LOCAL_API_KEY.
    In production mode: raises 501 (OIDC not yet implemented in this milestone).
    """
    if not credentials:
        raise _local_mode_rejection()

    token = credentials.credentials

    if settings.is_production():
        # OIDC verification is a future milestone.
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OIDC authentication not yet configured. "
                   "Set AUTH_MODE=local for demo, or configure OIDC parameters.",
        )

    if settings.is_local_demo():
        if token == settings.local_api_key:
            return UserContext(role=ROLE_ANALYST, user_id="local-demo-user", auth_mode="local")
        raise _local_mode_rejection()

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OIDC authentication not yet configured. Set AUTH_MODE=local for demo.",
    )


def require_role(required_role: str):
    """Dependency factory: enforce a minimum role for protected endpoints.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(user=Depends(require_role("admin"))):
            ...
    """
    def _role_checker(
        user: UserContext = Depends(get_current_user),
    ) -> UserContext:
        if not _role_requires_min(user.role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {required_role}",
            )
        return user

    return _role_checker