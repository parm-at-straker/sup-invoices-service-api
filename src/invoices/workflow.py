"""Status workflow validation for invoices and purchase orders."""

from .enums import InvoiceStatus, POStatus


class InvalidStatusTransitionError(Exception):
    """Invalid status transition exception."""
    pass


# Valid status transitions for invoices
INVOICE_STATUS_TRANSITIONS = {
    InvoiceStatus.DRAFT: [
        InvoiceStatus.PENDING,
        InvoiceStatus.SENT,
        InvoiceStatus.CANCELLED,
    ],
    InvoiceStatus.PENDING: [
        InvoiceStatus.SENT,
        InvoiceStatus.CANCELLED,
    ],
    InvoiceStatus.SENT: [
        InvoiceStatus.PAID,
        InvoiceStatus.OVERDUE,
        InvoiceStatus.CANCELLED,
    ],
    InvoiceStatus.PAID: [
        InvoiceStatus.REFUNDED,
    ],
    InvoiceStatus.OVERDUE: [
        InvoiceStatus.PAID,
        InvoiceStatus.CANCELLED,
    ],
    InvoiceStatus.CANCELLED: [],  # Terminal state
    InvoiceStatus.REFUNDED: [],  # Terminal state
}


# Valid status transitions for purchase orders
PO_STATUS_TRANSITIONS = {
    POStatus.PENDING: [
        POStatus.ACCEPTED,
        POStatus.DECLINED,
        POStatus.CANCELLED,
    ],
    POStatus.ACCEPTED: [
        POStatus.IN_PROGRESS,
        POStatus.CANCELLED,
    ],
    POStatus.IN_PROGRESS: [
        POStatus.COMPLETED,
        POStatus.CANCELLED,
    ],
    POStatus.COMPLETED: [
        POStatus.APPROVED,
    ],
    POStatus.APPROVED: [
        POStatus.PAID,
    ],
    POStatus.PAID: [],  # Terminal state
    POStatus.DECLINED: [],  # Terminal state
    POStatus.CANCELLED: [],  # Terminal state
    POStatus.EXPIRED: [],  # Terminal state
    POStatus.DISPUTED: [
        POStatus.APPROVED,
        POStatus.CANCELLED,
    ],
}


def validate_invoice_status_transition(
    current_status: str, new_status: str
) -> bool:
    """Validate if invoice status transition is allowed.

    Args:
        current_status: Current invoice status
        new_status: New invoice status

    Returns:
        True if transition is valid

    Raises:
        InvalidStatusTransitionError: If transition is not allowed
    """
    # Allow if statuses are the same
    if current_status == new_status:
        return True

    # Convert string to enum if needed
    try:
        current = InvoiceStatus(current_status) if isinstance(current_status, str) else current_status
        new = InvoiceStatus(new_status) if isinstance(new_status, str) else new_status
    except ValueError:
        # If status is not in enum, allow it (for backward compatibility)
        return True

    # Check if transition is allowed
    allowed_transitions = INVOICE_STATUS_TRANSITIONS.get(current, [])
    if new not in allowed_transitions:
        raise InvalidStatusTransitionError(
            f"Cannot transition invoice from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {[s.value for s in allowed_transitions]}"
        )

    return True


def validate_po_status_transition(current_status: str, new_status: str) -> bool:
    """Validate if purchase order status transition is allowed.

    Args:
        current_status: Current PO status
        new_status: New PO status

    Returns:
        True if transition is valid

    Raises:
        InvalidStatusTransitionError: If transition is not allowed
    """
    # Allow if statuses are the same
    if current_status == new_status:
        return True

    # Convert string to enum if needed
    try:
        current = POStatus(current_status) if isinstance(current_status, str) else current_status
        new = POStatus(new_status) if isinstance(new_status, str) else new_status
    except ValueError:
        # If status is not in enum, allow it (for backward compatibility)
        return True

    # Check if transition is allowed
    allowed_transitions = PO_STATUS_TRANSITIONS.get(current, [])
    if new not in allowed_transitions:
        raise InvalidStatusTransitionError(
            f"Cannot transition purchase order from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {[s.value for s in allowed_transitions]}"
        )

    return True
