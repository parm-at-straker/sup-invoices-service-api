"""Pytest configuration and fixtures for Invoice/Purchase Order Service tests."""

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

# Set environment variables before importing application modules
os.environ["ENVIRONMENT"] = "local"
os.environ["DEBUG"] = "false"
os.environ.setdefault("DB_HOST_franchise", "localhost")
os.environ.setdefault("DB_HOST_franchise_readonly", "localhost")
os.environ.setdefault("DB_PORT_franchise", "3306")
os.environ.setdefault("DB_PORT_franchise_readonly", "3306")
os.environ.setdefault("DB_USER_franchise", "root")
os.environ.setdefault("DB_USER_franchise_readonly", "root")
os.environ.setdefault("DB_PASSWORD_franchise", "test")
os.environ.setdefault("DB_PASSWORD_franchise_readonly", "test")

from src.invoices.models import Invoice, PurchaseOrder, InvoiceItem, InvoiceGroup, POMilestone, PODisbursementItem


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = MagicMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def sample_invoice():
    """Create a sample invoice."""
    return Invoice(
        obj_uuid="INVOICE-UUID-1234",
        id=1,
        jobid=12345,
        currency="USD",
        amount=1000.00,
        amount_nett=900.00,
        status="Draft",
        invoice_type="Tax Invoice",
        created=datetime(2025, 1, 1, tzinfo=timezone.utc),
        modified=datetime(2025, 1, 1, tzinfo=timezone.utc),
        deleted=False,
    )


@pytest.fixture
def sample_purchase_order():
    """Create a sample purchase order."""
    return PurchaseOrder(
        obj_uuid="PO-UUID-1234",
        translatorid="TRANSLATOR-UUID-1234",
        tp_job="JOB-UUID-1234",
        amount=500.00,
        amount_nett=450.00,
        currency="USD",
        status="Pending",
        created=datetime(2025, 1, 1, tzinfo=timezone.utc),
        modified=datetime(2025, 1, 1, tzinfo=timezone.utc),
        is_deleted=False,
    )


@pytest.fixture
def sample_invoice_item():
    """Create a sample invoice item."""
    return InvoiceItem(
        obj_uuid="ITEM-UUID-1234",
        invoice_uuid="INVOICE-UUID-1234",
        item_type="language_pair",
        source_lang="en",
        target_lang="es",
        amount_nett=100.00,
        currency="USD",
        created=datetime(2025, 1, 1, tzinfo=timezone.utc),
        modified=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_invoice_group():
    """Create a sample invoice group."""
    return InvoiceGroup(
        obj_uuid="GROUP-UUID-1234",
        id=1,
        companyid="COMPANY-UUID-1234",
        currency="USD",
        amount=2000.00,
        amount_nett=1800.00,
        status="Draft",
        invoice_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        created=datetime(2025, 1, 1, tzinfo=timezone.utc),
        modified=datetime(2025, 1, 1, tzinfo=timezone.utc),
        deleted=False,
    )


@pytest.fixture
def sample_po_milestone():
    """Create a sample PO milestone."""
    return POMilestone(
        obj_uuid="MILESTONE-UUID-1234",
        tp_purchaseorder="PO-UUID-1234",
        milestone=25,
        date_completed=datetime(2025, 1, 1, tzinfo=timezone.utc),
        confirmed=1,
        created=datetime(2025, 1, 1, tzinfo=timezone.utc),
        modified=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_po_disbursement():
    """Create a sample PO disbursement item."""
    return PODisbursementItem(
        obj_uuid="DISBURSEMENT-UUID-1234",
        po_uuid="PO-UUID-1234",
        item_type="DTP",
        item_type_info="Desktop Publishing",
        no_of_units=5,
        rate_per_unit=50.00,
        total_cost=250.00,
        created=datetime(2025, 1, 1, tzinfo=timezone.utc),
        modified=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
