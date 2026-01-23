"""Tests for the SalesOrderService."""

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

# Set environment before imports
os.environ["ENVIRONMENT"] = "local"
os.environ["DEBUG"] = "false"

from src.salesorders.service import (
    SalesOrderService,
    SalesOrderNotFoundError,
)
from src.salesorders.schemas import (
    SalesOrderCreate,
    SalesOrderUpdate,
    TransformToInvoiceRequest,
)


class TestSalesOrderService:
    """Tests for SalesOrderService."""

    @pytest.mark.asyncio
    async def test_create_sales_order(self, mock_db, sample_invoice):
        """Test creating a sales order."""
        # Mock the get_sales_order call that happens after creation
        mock_result = MagicMock()
        mock_row = MagicMock()
        sample_invoice.invoice_type = "Pro Forma"
        mock_row.__getitem__ = lambda self, key: sample_invoice if key == 0 else "JOB-UUID-1234"
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        def mock_refresh(so):
            so.obj_uuid = "NEW-SO-UUID"
            so.jobid = 12345
            so.invoice_type = "Pro Forma"

        mock_db.refresh.side_effect = mock_refresh

        so_data = SalesOrderCreate(
            jobid=12345,
            amount_nett=900.00,
            currency="USD",
            invoice_type="Pro Forma",
        )

        service = SalesOrderService(mock_db)
        result = await service.create_sales_order(so_data, "user-123")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_sales_order_not_found(self, mock_db):
        """Test getting a non-existent sales order."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        service = SalesOrderService(mock_db)
        result = await service.get_sales_order("NON-EXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_transform_to_invoice(self, mock_db, sample_invoice):
        """Test transforming a sales order to an invoice."""
        sample_invoice.invoice_type = "Pro Forma"
        sample_invoice.status = "Draft"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_invoice
        mock_db.execute.return_value = mock_result

        # Mock get_sales_order after transform
        mock_get_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_invoice if key == 0 else "JOB-UUID-1234"
        mock_get_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_get_result

        transform_data = TransformToInvoiceRequest(
            invoice_type="Tax Invoice",
            due_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
        )

        service = SalesOrderService(mock_db)
        result = await service.transform_to_invoice(
            "SO-UUID-1234", transform_data, "user-123"
        )

        mock_db.commit.assert_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_cancel_sales_order(self, mock_db, sample_invoice):
        """Test cancelling a sales order."""
        sample_invoice.invoice_type = "Pro Forma"
        sample_invoice.status = "Draft"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_invoice
        mock_db.execute.return_value = mock_result

        # Mock get_sales_order after cancel
        mock_get_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_invoice if key == 0 else "JOB-UUID-1234"
        mock_get_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_get_result

        service = SalesOrderService(mock_db)
        result = await service.cancel_sales_order(
            "SO-UUID-1234", "Cancelled by user", "user-123"
        )

        mock_db.commit.assert_called()
        assert result is not None
        assert result.get("status") == "Cancelled"
