"""Tests for status workflow validation."""

import os
import pytest

# Set environment before imports
os.environ["ENVIRONMENT"] = "local"
os.environ["DEBUG"] = "false"

from src.invoices.workflow import (
    InvalidStatusTransitionError,
    validate_invoice_status_transition,
    validate_po_status_transition,
)
from src.invoices.enums import InvoiceStatus, POStatus


class TestInvoiceStatusWorkflow:
    """Tests for invoice status transitions."""

    def test_valid_transition_draft_to_pending(self):
        """Test valid transition from Draft to Pending."""
        result = validate_invoice_status_transition("Draft", "Pending")
        assert result is True

    def test_valid_transition_pending_to_sent(self):
        """Test valid transition from Pending to Sent."""
        result = validate_invoice_status_transition("Pending", "Sent")
        assert result is True

    def test_valid_transition_sent_to_paid(self):
        """Test valid transition from Sent to Paid."""
        result = validate_invoice_status_transition("Sent", "Paid")
        assert result is True

    def test_invalid_transition_draft_to_paid(self):
        """Test invalid transition from Draft to Paid."""
        with pytest.raises(InvalidStatusTransitionError):
            validate_invoice_status_transition("Draft", "Paid")

    def test_same_status_allowed(self):
        """Test that same status is allowed."""
        result = validate_invoice_status_transition("Draft", "Draft")
        assert result is True

    def test_terminal_state_cancelled(self):
        """Test that Cancelled is a terminal state."""
        with pytest.raises(InvalidStatusTransitionError):
            validate_invoice_status_transition("Cancelled", "Paid")


class TestPOStatusWorkflow:
    """Tests for purchase order status transitions."""

    def test_valid_transition_pending_to_accepted(self):
        """Test valid transition from Pending to Accepted."""
        result = validate_po_status_transition("Pending", "Accepted")
        assert result is True

    def test_valid_transition_accepted_to_in_progress(self):
        """Test valid transition from Accepted to In Progress."""
        result = validate_po_status_transition("Accepted", "In Progress")
        assert result is True

    def test_valid_transition_completed_to_approved(self):
        """Test valid transition from Completed to Approved."""
        result = validate_po_status_transition("Completed", "Approved")
        assert result is True

    def test_invalid_transition_pending_to_paid(self):
        """Test invalid transition from Pending to Paid."""
        with pytest.raises(InvalidStatusTransitionError):
            validate_po_status_transition("Pending", "Paid")

    def test_terminal_state_paid(self):
        """Test that Paid is a terminal state."""
        with pytest.raises(InvalidStatusTransitionError):
            validate_po_status_transition("Paid", "Approved")
