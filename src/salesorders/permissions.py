"""Sales Order permissions and authorization."""

from ..invoices.enums import UserRole
from .enums import SalesOrderPermission


def check_sales_order_permission(user_role: str, permission: SalesOrderPermission) -> bool:
    """Check if user role has sales order permission.

    Args:
        user_role: The user's role
        permission: The permission to check

    Returns:
        True if user has permission, False otherwise
    """
    role_permissions = {
        UserRole.ADMIN: list(SalesOrderPermission),
        UserRole.FINANCE: list(SalesOrderPermission),
        UserRole.TEAM_LEAD: [
            SalesOrderPermission.CREATE,
            SalesOrderPermission.READ,
            SalesOrderPermission.UPDATE,
            SalesOrderPermission.TRANSFORM,
            SalesOrderPermission.CANCEL,
        ],
        UserRole.TEAM_MEMBER: [
            SalesOrderPermission.READ,
            SalesOrderPermission.UPDATE,  # Limited fields
        ],
    }
    return permission in role_permissions.get(user_role, [])


def require_sales_order_permission(
    user_role: str, permission: SalesOrderPermission
) -> None:
    """Require a sales order permission, raise exception if not granted.

    Args:
        user_role: The user's role
        permission: The permission required

    Raises:
        PermissionError: If user doesn't have the required permission
    """
    if not check_sales_order_permission(user_role, permission):
        raise PermissionError(
            f"User with role '{user_role}' does not have permission '{permission.value}'"
        )
