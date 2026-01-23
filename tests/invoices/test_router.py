"""Tests for invoice router endpoints."""

import os
import pytest
from fastapi.testclient import TestClient

# Set environment before imports
os.environ["ENVIRONMENT"] = "local"
os.environ["DEBUG"] = "false"

from src.main import app

client = TestClient(app)


class TestInvoiceRouter:
    """Tests for invoice router endpoints."""

    def test_list_invoices_endpoint(self):
        """Test listing invoices endpoint."""
        response = client.get("/v1/invoices")
        # Should return 200 or 401 depending on auth
        assert response.status_code in [200, 401]

    def test_get_invoice_endpoint_not_found(self):
        """Test getting a non-existent invoice."""
        response = client.get("/v1/invoices/NON-EXISTENT-UUID")
        # Should return 404 or 401 depending on auth
        assert response.status_code in [404, 401]

    def test_create_invoice_endpoint_validation(self):
        """Test invoice creation validation."""
        # Missing required fields should return 422
        response = client.post("/v1/invoices", json={})
        assert response.status_code in [400, 401, 422]


class TestInvoiceItemRouter:
    """Tests for invoice item router endpoints."""

    def test_list_invoice_items_endpoint(self):
        """Test listing invoice items endpoint."""
        response = client.get("/v1/invoices/INVOICE-UUID-1234/items")
        # Should return 404 (invoice not found) or 401 (unauth)
        assert response.status_code in [404, 401]


class TestInvoiceGroupRouter:
    """Tests for invoice group router endpoints."""

    def test_list_invoice_groups_endpoint(self):
        """Test listing invoice groups endpoint."""
        response = client.get("/v1/invoice-groups")
        # Should return 200 or 401 depending on auth
        assert response.status_code in [200, 401]


class TestPurchaseOrderRouter:
    """Tests for purchase order router endpoints."""

    def test_list_purchase_orders_endpoint(self):
        """Test listing purchase orders endpoint."""
        response = client.get("/v1/purchase-orders")
        # Should return 200 or 401 depending on auth
        assert response.status_code in [200, 401]

    def test_get_purchase_order_endpoint_not_found(self):
        """Test getting a non-existent purchase order."""
        response = client.get("/v1/purchase-orders/NON-EXISTENT-UUID")
        # Should return 404 or 401 depending on auth
        assert response.status_code in [404, 401]


class TestSalesOrderRouter:
    """Tests for sales order router endpoints."""

    def test_list_sales_orders_endpoint(self):
        """Test listing sales orders endpoint."""
        response = client.get("/v1/sales-orders")
        # Should return 200 or 401 depending on auth
        assert response.status_code in [200, 401]

    def test_get_sales_order_endpoint_not_found(self):
        """Test getting a non-existent sales order."""
        response = client.get("/v1/sales-orders/NON-EXISTENT-UUID")
        # Should return 404 or 401 depending on auth
        assert response.status_code in [404, 401]
