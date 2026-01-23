"""Sales Order related enums."""

from enum import Enum


class SalesOrderStatus(str, Enum):
    """Sales Order status values."""

    DRAFT = "Draft"
    PENDING = "Pending"
    SENT = "Sent"
    CANCELLED = "Cancelled"
    TRANSFORMED = "Transformed"  # When transformed to invoice


class SalesOrderPermission(str, Enum):
    """Sales Order permissions."""

    CREATE = "sales_orders:create"
    READ = "sales_orders:read"
    UPDATE = "sales_orders:update"
    DELETE = "sales_orders:delete"
    TRANSFORM = "sales_orders:transform"
    CANCEL = "sales_orders:cancel"
