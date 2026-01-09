"""Invoice and Purchase Order related enums."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice status values."""

    DRAFT = "Draft"
    PENDING = "Pending"
    SENT = "Sent"
    PAID = "Paid"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"


class POStatus(str, Enum):
    """Purchase Order status values."""

    PENDING = "Pending"
    ACCEPTED = "Accepted"
    DECLINED = "Declined"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    APPROVED = "Approved"
    PAID = "Paid"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"
    DISPUTED = "Disputed"


class InvoicePermission(str, Enum):
    """Invoice permissions."""

    CREATE = "invoices:create"
    READ = "invoices:read"
    UPDATE = "invoices:update"
    DELETE = "invoices:delete"
    APPROVE = "invoices:approve"
    VIEW_FINANCIAL = "invoices:view_financial"


class POPermission(str, Enum):
    """Purchase Order permissions."""

    CREATE = "purchase_orders:create"
    READ = "purchase_orders:read"
    UPDATE = "purchase_orders:update"
    DELETE = "purchase_orders:delete"
    APPROVE = "purchase_orders:approve"
    VIEW_FINANCIAL = "purchase_orders:view_financial"


class UserRole(str, Enum):
    """User roles."""

    ADMIN = "admin"
    TEAM_LEAD = "team_lead"
    TEAM_MEMBER = "team_member"
    FINANCE = "finance"

