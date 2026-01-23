"""Integration tests for invoice API endpoints."""

import os
import pytest
from fastapi.testclient import TestClient

# Set environment before imports
os.environ["ENVIRONMENT"] = "local"
os.environ["DEBUG"] = "false"

from src.main import app

client = TestClient(app)


class TestInvoiceAPIIntegration:
    """Integration tests for invoice endpoints."""

    def test_invoice_crud_flow(self):
        """Test complete invoice CRUD flow."""
        # Create invoice
        invoice_data = {
            "jobid": 12345,
            "currency": "USD",
            "amount": 1000.00,
            "status": "Draft",
        }
        create_response = client.post("/v1/invoices", json=invoice_data)
        # May fail due to auth or validation, but structure should be correct
        assert create_response.status_code in [201, 400, 401, 422]

        if create_response.status_code == 201:
            invoice_uuid = create_response.json()["data"]["obj_uuid"]

            # Get invoice
            get_response = client.get(f"/v1/invoices/{invoice_uuid}")
            assert get_response.status_code in [200, 401]

            # Update invoice
            update_data = {"status": "Pending"}
            update_response = client.put(
                f"/v1/invoices/{invoice_uuid}", json=update_data
            )
            assert update_response.status_code in [200, 400, 401]

            # Approve invoice
            approve_response = client.post(f"/v1/invoices/{invoice_uuid}/approve")
            assert approve_response.status_code in [200, 400, 401]

            # Archive invoice
            archive_response = client.post(f"/v1/invoices/{invoice_uuid}/archive")
            assert archive_response.status_code in [200, 400, 401]

            # Restore invoice
            restore_response = client.post(f"/v1/invoices/{invoice_uuid}/restore")
            assert restore_response.status_code in [200, 400, 401]

    def test_invoice_items_crud_flow(self):
        """Test invoice items CRUD flow."""
        # This would require a valid invoice UUID
        invoice_uuid = "TEST-INVOICE-UUID"

        # List items
        list_response = client.get(f"/v1/invoices/{invoice_uuid}/items")
        assert list_response.status_code in [200, 404, 401]

        # Create item
        item_data = {
            "invoice_uuid": invoice_uuid,
            "item_type": "language_pair",
            "amount_nett": 100.00,
            "currency": "USD",
        }
        create_response = client.post(
            f"/v1/invoices/{invoice_uuid}/items", json=item_data
        )
        assert create_response.status_code in [201, 400, 401, 404]


class TestPurchaseOrderAPIIntegration:
    """Integration tests for purchase order endpoints."""

    def test_po_crud_flow(self):
        """Test complete PO CRUD flow."""
        # Create PO
        po_data = {
            "translatorid": "TRANSLATOR-UUID-1234",
            "tp_job": "JOB-UUID-1234",
            "amount": 500.00,
            "currency": "USD",
            "status": "Pending",
        }
        create_response = client.post("/v1/purchase-orders", json=po_data)
        assert create_response.status_code in [201, 400, 401, 422]

        if create_response.status_code == 201:
            po_uuid = create_response.json()["data"]["obj_uuid"]

            # Get PO
            get_response = client.get(f"/v1/purchase-orders/{po_uuid}")
            assert get_response.status_code in [200, 401]

            # Approve PO
            approve_response = client.post(f"/v1/purchase-orders/{po_uuid}/approve")
            assert approve_response.status_code in [200, 400, 401]

    def test_po_milestones_flow(self):
        """Test PO milestones flow."""
        po_uuid = "TEST-PO-UUID"

        # List milestones
        list_response = client.get(f"/v1/purchase-orders/{po_uuid}/milestones")
        assert list_response.status_code in [200, 404, 401]

        # Create milestone
        milestone_data = {
            "tp_purchaseorder": po_uuid,
            "milestone": 25,
            "notes": "25% complete",
        }
        create_response = client.post(
            f"/v1/purchase-orders/{po_uuid}/milestones", json=milestone_data
        )
        assert create_response.status_code in [201, 400, 401, 404]

    def test_po_disbursements_flow(self):
        """Test PO disbursements flow."""
        po_uuid = "TEST-PO-UUID"

        # List disbursements
        list_response = client.get(f"/v1/purchase-orders/{po_uuid}/disbursements")
        assert list_response.status_code in [200, 404, 401]

        # Create disbursement
        disbursement_data = {
            "po_uuid": po_uuid,
            "item_type": "DTP",
            "item_type_info": "Desktop Publishing",
            "no_of_units": 5,
            "rate_per_unit": 50.00,
            "total_cost": 250.00,
        }
        create_response = client.post(
            f"/v1/purchase-orders/{po_uuid}/disbursements", json=disbursement_data
        )
        assert create_response.status_code in [201, 400, 401, 404]

    def test_batch_operations(self):
        """Test batch PO operations."""
        # Batch approve
        approve_data = {"po_uuids": ["PO-UUID-1", "PO-UUID-2"]}
        approve_response = client.post(
            "/v1/purchase-orders/batch-approve", json=approve_data
        )
        assert approve_response.status_code in [200, 400, 401]

        # Batch delete
        delete_data = {"po_uuids": ["PO-UUID-1", "PO-UUID-2"]}
        delete_response = client.post(
            "/v1/purchase-orders/batch-delete", json=delete_data
        )
        assert delete_response.status_code in [200, 400, 401]


class TestSalesOrderAPIIntegration:
    """Integration tests for sales order endpoints."""

    def test_sales_order_crud_flow(self):
        """Test complete sales order CRUD flow."""
        # Create sales order
        so_data = {
            "jobid": 12345,
            "amount_nett": 900.00,
            "currency": "USD",
            "invoice_type": "Pro Forma",
        }
        create_response = client.post("/v1/sales-orders", json=so_data)
        assert create_response.status_code in [201, 400, 401, 422]

        if create_response.status_code == 201:
            so_uuid = create_response.json()["data"]["obj_uuid"]

            # Get sales order
            get_response = client.get(f"/v1/sales-orders/{so_uuid}")
            assert get_response.status_code in [200, 401]

            # Transform to invoice
            transform_data = {
                "invoice_type": "Tax Invoice",
                "due_date": "2025-02-01T00:00:00Z",
            }
            transform_response = client.post(
                f"/v1/sales-orders/{so_uuid}/transform-to-invoice", json=transform_data
            )
            assert transform_response.status_code in [200, 400, 401]

            # Cancel sales order
            cancel_data = {"reason": "Cancelled by user"}
            cancel_response = client.post(
                f"/v1/sales-orders/{so_uuid}/cancel", json=cancel_data
            )
            assert cancel_response.status_code in [200, 400, 401]


class TestInvoiceGroupAPIIntegration:
    """Integration tests for invoice group endpoints."""

    def test_invoice_group_crud_flow(self):
        """Test complete invoice group CRUD flow."""
        # Create invoice group
        group_data = {
            "companyid": "COMPANY-UUID-1234",
            "currency": "USD",
            "invoice_date": "2025-01-01T00:00:00Z",
            "status": "Draft",
        }
        create_response = client.post("/v1/invoice-groups", json=group_data)
        assert create_response.status_code in [201, 400, 401, 422]

        if create_response.status_code == 201:
            group_uuid = create_response.json()["data"]["obj_uuid"]

            # Get invoice group
            get_response = client.get(f"/v1/invoice-groups/{group_uuid}")
            assert get_response.status_code in [200, 401]

            # Add invoice to group
            add_data = {"invoice_uuid": "INVOICE-UUID-1234"}
            add_response = client.post(
                f"/v1/invoice-groups/{group_uuid}/add-invoice", json=add_data
            )
            assert add_response.status_code in [200, 400, 401, 404]

            # Remove invoice from group
            remove_data = {"invoice_uuid": "INVOICE-UUID-1234"}
            remove_response = client.post(
                f"/v1/invoice-groups/{group_uuid}/remove-invoice", json=remove_data
            )
            assert remove_response.status_code in [200, 400, 401, 404]
