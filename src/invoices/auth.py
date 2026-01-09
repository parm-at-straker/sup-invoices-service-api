"""Authentication and authorization dependencies."""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from .enums import UserRole


async def get_current_user_role(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> dict:
    """Get current user and role from JWT token or API key.

    Args:
        authorization: Bearer token from Authorization header
        x_api_key: API key from X-API-Key header

    Returns:
        Dictionary with user info including role

    Raises:
        HTTPException: If authentication fails
    """
    # For now, we'll use a simple approach
    # In production, this should validate JWT tokens or API keys
    # and extract user information from the API Gateway

    # If API key is provided, treat as service-to-service
    if x_api_key:
        # TODO: Validate API key against configured service keys
        return {
            "user_id": "service",
            "role": UserRole.ADMIN,
            "authenticated": True,
        }

    # If Authorization header is provided, extract user from token
    if authorization:
        try:
            # TODO: Validate JWT token and extract user info
            # For now, return a mock user
            # In production, this should call the API Gateway or auth service
            token = authorization.replace("Bearer ", "")
            # Mock user extraction - replace with actual JWT validation
            return {
                "user_id": "user-123",  # Extract from token
                "role": UserRole.TEAM_LEAD,  # Extract from token
                "authenticated": True,
            }
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def require_role(required_role: UserRole):
    """Dependency factory to require a specific role.

    Args:
        required_role: The required role

    Returns:
        Dependency function
    """

    async def role_checker(user: dict = Depends(get_current_user_role)) -> dict:
        user_role = user.get("role")
        if user_role != required_role and user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role.value} role",
            )
        return user

    return role_checker

