"""Tests for the InvoiceService."""

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

# Set environment before imports
os.environ["ENVIRONMENT"] = "local"
os.environ["DEBUG"] = "false"

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.invoices.service import (
    InvoiceService,
    InvoiceNotFoundError,
    InvoiceGroupNotFoundError,
)
from src.invoices.schemas import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceItemCreate,
    InvoiceItemUpdate,
    InvoiceGroupCreate,
    InvoiceGroupUpdate,
)
from src.invoices.workflow import InvalidStatusTransitionError


class TestInvoiceService:
    """Tests for InvoiceService."""

    @pytest.mark.asyncio
    async def test_create_invoice(self, mock_db, sample_invoice):
        """Test creating an invoice."""
        # Mock the get_invoice call that happens after creation
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_invoice if key == 0 else "JOB-UUID-1234"
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        def mock_refresh(invoice):
            invoice.obj_uuid = "NEW-INVOICE-UUID"
            invoice.jobid = 12345

        mock_db.refresh.side_effect = mock_refresh

        invoice_data = InvoiceCreate(
            jobid=12345,
            currency="USD",
            amount=1000.00,
            status="Draft",
        )

        service = InvoiceService(mock_db)
        result = await service.create_invoice(invoice_data, "user-123")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_invoice_not_found(self, mock_db):
        """Test getting a non-existent invoice."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        service = InvoiceService(mock_db)
        result = await service.get_invoice("NON-EXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_invoice_or_404_raises(self, mock_db):
        """Test get_invoice_or_404 raises when invoice not found."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        service = InvoiceService(mock_db)

        with pytest.raises(InvoiceNotFoundError):
            await service.get_invoice_or_404("NON-EXISTENT")

    @pytest.mark.asyncio
    async def test_update_invoice_status_transition(self, mock_db, sample_invoice):
        """Test updating invoice with valid status transition."""
        # Mock get_invoice_or_404
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_invoice if key == 0 else "JOB-UUID-1234"
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        # Mock the update query
        mock_update_result = MagicMock()
        mock_update_result.scalar_one_or_none.return_value = sample_invoice
        mock_db.execute.return_value = mock_update_result

        invoice_data = InvoiceUpdate(status="Pending")

        service = InvoiceService(mock_db)
        result = await service.update_invoice("INVOICE-UUID-1234", invoice_data, "user-123")

        mock_db.commit.assert_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_approve_invoice(self, mock_db, sample_invoice):
        """Test approving an invoice."""
        # Mock get_invoice_or_404
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_invoice if key == 0 else "JOB-UUID-1234"
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        # Mock the update query
        mock_update_result = MagicMock()
        mock_update_result.scalar_one_or_none.return_value = sample_invoice
        mock_db.execute.return_value = mock_update_result

        service = InvoiceService(mock_db)
        result = await service.approve_invoice("INVOICE-UUID-1234", "user-123")

        mock_db.commit.assert_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_invoice(self, mock_db, sample_invoice):
        """Test deleting an invoice."""
        # Mock get_invoice_or_404
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_invoice if key == 0 else "JOB-UUID-1234"
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        # Mock the update query
        mock_update_result = MagicMock()
        mock_update_result.scalar_one_or_none.return_value = sample_invoice
        mock_db.execute.return_value = mock_update_result

        service = InvoiceService(mock_db)
        await service.delete_invoice("INVOICE-UUID-1234", "user-123")

        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_list_invoice_items(self, mock_db):
        """Test listing invoice items."""
        from src.invoices.models import InvoiceItem

        mock_item = InvoiceItem(
            obj_uuid="ITEM-UUID-1234",
            invoice_uuid="INVOICE-UUID-1234",
            item_type="language_pair",
            amount_nett=100.00,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_item]
        mock_db.execute.return_value = mock_result

        service = InvoiceService(mock_db)
        items = await service.list_invoice_items("INVOICE-UUID-1234")

        assert len(items) == 1
        assert items[0]["obj_uuid"] == "ITEM-UUID-1234"

    @pytest.mark.asyncio
    async def test_create_invoice_item(self, mock_db):
        """Test creating an invoice item."""
        # Mock get_invoice_or_404
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_invoice = MagicMock()
        mock_invoice.obj_uuid = "INVOICE-UUID-1234"
        mock_row.__getitem__ = lambda self, key: mock_invoice if key == 0 else "JOB-UUID-1234"
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        def mock_refresh(item):
            item.obj_uuid = "NEW-ITEM-UUID"

        mock_db.refresh.side_effect = mock_refresh

        item_data = InvoiceItemCreate(
            invoice_uuid="INVOICE-UUID-1234",
            item_type="language_pair",
            amount_nett=100.00,
            currency="USD",
        )

        service = InvoiceService(mock_db)
        result = await service.create_invoice_item(
            "INVOICE-UUID-1234", item_data, "user-123"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_create_invoice_group(self, mock_db):
        """Test creating an invoice group."""
        from src.invoices.models import InvoiceGroup

        def mock_refresh(group):
            group.obj_uuid = "NEW-GROUP-UUID"
            group.id = 1

        mock_db.refresh.side_effect = mock_refresh

        group_data = InvoiceGroupCreate(
            companyid="COMPANY-UUID-1234",
            currency="USD",
            invoice_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            status="Draft",
        )

        service = InvoiceService(mock_db)
        result = await service.create_invoice_group(group_data, "user-123")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_invoice_group_not_found(self, mock_db):
        """Test getting a non-existent invoice group."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = InvoiceService(mock_db)
        result = await service.get_invoice_group("NON-EXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_archive_invoice(self, mock_db, sample_invoice):
        """Test archiving an invoice."""
        # Mock get_invoice_or_404
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_invoice if key == 0 else "JOB-UUID-1234"
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        # Mock the update query
        mock_update_result = MagicMock()
        mock_update_result.scalar_one_or_none.return_value = sample_invoice
        mock_db.execute.return_value = mock_update_result

        service = InvoiceService(mock_db)
        result = await service.archive_invoice("INVOICE-UUID-1234", "user-123")

        mock_db.commit.assert_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_restore_invoice(self, mock_db, sample_invoice):
        """Test restoring an archived invoice."""
        sample_invoice.deleted = True
        sample_invoice.status = "Archived"

        # Mock get_invoice (for restore, we get even deleted invoices)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_invoice
        mock_db.execute.return_value = mock_result

        # Mock get_invoice after restore
        mock_get_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_invoice if key == 0 else "JOB-UUID-1234"
        mock_get_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_get_result

        service = InvoiceService(mock_db)
        result = await service.restore_invoice("INVOICE-UUID-1234", "user-123")

        mock_db.commit.assert_called()
        assert result is not None
