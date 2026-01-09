"""Invoice and Purchase Order permissions and authorization."""

from .enums import InvoicePermission, POPermission, UserRole


def check_invoice_permission(user_role: str, permission: InvoicePermission) -> bool:
    """Check if user role has invoice permission.

    Args:
        user_role: The user's role
        permission: The permission to check

    Returns:
        True if user has permission, False otherwise
    """
    role_permissions = {
        UserRole.ADMIN: list(InvoicePermission),
        UserRole.FINANCE: list(InvoicePermission),
        UserRole.TEAM_LEAD: [
            InvoicePermission.CREATE,
            InvoicePermission.READ,
            InvoicePermission.UPDATE,
            InvoicePermission.APPROVE,
        ],
        UserRole.TEAM_MEMBER: [
            InvoicePermission.READ,
            InvoicePermission.UPDATE,  # Limited fields
        ],
    }
    return permission in role_permissions.get(user_role, [])


def require_invoice_permission(
    user_role: str, permission: InvoicePermission
) -> None:
    """Require an invoice permission, raise exception if not granted.

    Args:
        user_role: The user's role
        permission: The permission required

    Raises:
        PermissionError: If user doesn't have the required permission
    """
    if not check_invoice_permission(user_role, permission):
        raise PermissionError(
            f"User with role '{user_role}' does not have permission '{permission.value}'"
        )


def check_po_permission(user_role: str, permission: POPermission) -> bool:
    """Check if user role has purchase order permission.

    Args:
        user_role: The user's role
        permission: The permission to check

    Returns:
        True if user has permission, False otherwise
    """
    role_permissions = {
        UserRole.ADMIN: list(POPermission),
        UserRole.FINANCE: list(POPermission),
        UserRole.TEAM_LEAD: [
            POPermission.CREATE,
            POPermission.READ,
            POPermission.UPDATE,
            POPermission.APPROVE,
        ],
        UserRole.TEAM_MEMBER: [
            POPermission.READ,
            POPermission.UPDATE,  # Limited fields
        ],
    }
    return permission in role_permissions.get(user_role, [])


def require_po_permission(user_role: str, permission: POPermission) -> None:
    """Require a purchase order permission, raise exception if not granted.

    Args:
        user_role: The user's role
        permission: The permission required

    Raises:
        PermissionError: If user doesn't have the required permission
    """
    if not check_po_permission(user_role, permission):
        raise PermissionError(
            f"User with role '{user_role}' does not have permission '{permission.value}'"
        )

