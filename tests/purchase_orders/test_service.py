"""Tests for the PurchaseOrderService."""

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

# Set environment before imports
os.environ["ENVIRONMENT"] = "local"
os.environ["DEBUG"] = "false"

from src.invoices.service import (
    PurchaseOrderService,
    PurchaseOrderNotFoundError,
)
from src.invoices.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
)
from src.invoices.workflow import InvalidStatusTransitionError


class TestPurchaseOrderService:
    """Tests for PurchaseOrderService."""

    @pytest.mark.asyncio
    async def test_create_purchase_order(self, mock_db, sample_purchase_order):
        """Test creating a purchase order."""
        # Mock the get_purchase_order call that happens after creation
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_purchase_order if key == 0 else 12345
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        def mock_refresh(po):
            po.obj_uuid = "NEW-PO-UUID"
            po.tp_job = "JOB-UUID-1234"

        mock_db.refresh.side_effect = mock_refresh

        po_data = PurchaseOrderCreate(
            translatorid="TRANSLATOR-UUID-1234",
            tp_job="JOB-UUID-1234",
            amount=500.00,
            currency="USD",
            status="Pending",
        )

        service = PurchaseOrderService(mock_db)
        result = await service.create_purchase_order(po_data, "user-123")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_purchase_order_not_found(self, mock_db):
        """Test getting a non-existent purchase order."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        service = PurchaseOrderService(mock_db)
        result = await service.get_purchase_order("NON-EXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_approve_purchase_order(self, mock_db, sample_purchase_order):
        """Test approving a purchase order."""
        # Mock get_purchase_order_or_404
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_purchase_order if key == 0 else 12345
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        # Mock the update query
        mock_update_result = MagicMock()
        mock_update_result.scalar_one_or_none.return_value = sample_purchase_order
        mock_db.execute.return_value = mock_update_result

        service = PurchaseOrderService(mock_db)
        result = await service.approve_purchase_order("PO-UUID-1234", "user-123")

        mock_db.commit.assert_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_list_po_milestones(self, mock_db):
        """Test listing PO milestones."""
        from src.invoices.models import POMilestone

        mock_milestone = POMilestone(
            obj_uuid="MILESTONE-UUID-1234",
            tp_purchaseorder="PO-UUID-1234",
            milestone=25,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_milestone]
        mock_db.execute.return_value = mock_result

        service = PurchaseOrderService(mock_db)
        milestones = await service.list_po_milestones("PO-UUID-1234")

        assert len(milestones) == 1
        assert milestones[0]["obj_uuid"] == "MILESTONE-UUID-1234"

    @pytest.mark.asyncio
    async def test_create_po_milestone(self, mock_db, sample_purchase_order):
        """Test creating a PO milestone."""
        # Mock get_purchase_order_or_404
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_purchase_order if key == 0 else 12345
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        def mock_refresh(milestone):
            milestone.obj_uuid = "NEW-MILESTONE-UUID"

        mock_db.refresh.side_effect = mock_refresh

        milestone_data = {
            "milestone": 25,
            "notes": "25% complete",
        }

        service = PurchaseOrderService(mock_db)
        result = await service.create_po_milestone(
            "PO-UUID-1234", milestone_data, "user-123"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_batch_approve_purchase_orders(self, mock_db, sample_purchase_order):
        """Test batch approving purchase orders."""
        # Mock get_purchase_order_or_404 and approve_purchase_order
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_purchase_order if key == 0 else 12345
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        mock_update_result = MagicMock()
        mock_update_result.scalar_one_or_none.return_value = sample_purchase_order
        mock_db.execute.return_value = mock_update_result

        service = PurchaseOrderService(mock_db)
        result = await service.batch_approve_purchase_orders(
            ["PO-UUID-1234", "PO-UUID-5678"], "user-123"
        )

        assert result["success_count"] >= 0
        assert result["failure_count"] >= 0
        assert "results" in result

    @pytest.mark.asyncio
    async def test_archive_purchase_order(self, mock_db, sample_purchase_order):
        """Test archiving a purchase order."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_purchase_order
        mock_db.execute.return_value = mock_result

        # Mock get_purchase_order after archive
        mock_get_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_purchase_order if key == 0 else 12345
        mock_get_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_get_result

        service = PurchaseOrderService(mock_db)
        result = await service.archive_purchase_order("PO-UUID-1234", "user-123")

        mock_db.commit.assert_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_restore_purchase_order(self, mock_db, sample_purchase_order):
        """Test restoring an archived purchase order."""
        sample_purchase_order.is_deleted = True
        sample_purchase_order.status = "Archived"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_purchase_order
        mock_db.execute.return_value = mock_result

        # Mock get_purchase_order after restore
        mock_get_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: sample_purchase_order if key == 0 else 12345
        mock_get_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_get_result

        service = PurchaseOrderService(mock_db)
        result = await service.restore_purchase_order("PO-UUID-1234", "user-123")

        mock_db.commit.assert_called()
        assert result is not None
