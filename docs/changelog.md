# Changelog

## 2026-01-23

- Added: Sales Order management module with full CRUD operations, transform-to-invoice, and cancel functionality (Parmpreet Singh, 2026-01-23)
- Added: Sales Order models, schemas, enums, service layer, router, and permissions module (Parmpreet Singh, 2026-01-23)
- Added: Sales Order API endpoints: GET /v1/sales-orders, GET /v1/sales-orders/{uuid}, POST /v1/sales-orders, PUT /v1/sales-orders/{uuid}, DELETE /v1/sales-orders/{uuid}, POST /v1/sales-orders/{uuid}/transform-to-invoice, POST /v1/sales-orders/{uuid}/cancel (Parmpreet Singh, 2026-01-23)
- Added: Invoice Line Items API endpoints: GET /v1/invoices/{uuid}/items, POST /v1/invoices/{uuid}/items, GET /v1/invoices/{uuid}/items/{item_uuid}, PUT /v1/invoices/{uuid}/items/{item_uuid}, DELETE /v1/invoices/{uuid}/items/{item_uuid} (Parmpreet Singh, 2026-01-23)
- Added: Invoice Groups API endpoints: GET /v1/invoice-groups, GET /v1/invoice-groups/{uuid}, POST /v1/invoice-groups, PUT /v1/invoice-groups/{uuid}, DELETE /v1/invoice-groups/{uuid}, POST /v1/invoice-groups/{uuid}/add-invoice, POST /v1/invoice-groups/{uuid}/remove-invoice (Parmpreet Singh, 2026-01-23)
- Added: PO Milestones API endpoints: GET /v1/purchase-orders/{uuid}/milestones, POST /v1/purchase-orders/{uuid}/milestones, PUT /v1/purchase-orders/{uuid}/milestones/{milestone_uuid} (Parmpreet Singh, 2026-01-23)
- Added: PO Disbursement Items model (PODisbursementItem) and API endpoints: GET /v1/purchase-orders/{uuid}/disbursements, POST /v1/purchase-orders/{uuid}/disbursements, PUT /v1/purchase-orders/{uuid}/disbursements/{item_uuid}, DELETE /v1/purchase-orders/{uuid}/disbursements/{item_uuid} (Parmpreet Singh, 2026-01-23)
- Added: Batch operations for purchase orders: POST /v1/purchase-orders/batch-approve, POST /v1/purchase-orders/batch-delete (Parmpreet Singh, 2026-01-23)
- Added: Archive and restore functionality for invoices and purchase orders: POST /v1/invoices/{uuid}/archive, POST /v1/invoices/{uuid}/restore, POST /v1/purchase-orders/{uuid}/archive, POST /v1/purchase-orders/{uuid}/restore (Parmpreet Singh, 2026-01-23)
- Added: Status workflow validation module with valid transition rules for invoices and purchase orders (Parmpreet Singh, 2026-01-23)
- Added: Invoice status workflow validation with transitions: Draft→Pending→Sent→Paid, with terminal states Cancelled and Refunded (Parmpreet Singh, 2026-01-23)
- Added: Purchase Order status workflow validation with transitions: Pending→Accepted→In Progress→Completed→Approved→Paid, with terminal states Declined, Cancelled, Expired (Parmpreet Singh, 2026-01-23)
- Added: Comprehensive unit tests for InvoiceService, PurchaseOrderService, and SalesOrderService with mock database sessions (Parmpreet Singh, 2026-01-23)
- Added: Unit tests for status workflow validation covering valid and invalid transitions (Parmpreet Singh, 2026-01-23)
- Added: Integration tests for all API endpoints covering CRUD flows, batch operations, and error handling (Parmpreet Singh, 2026-01-23)
- Changed: InvoiceService methods now return dict objects with enriched job_uuid field instead of model objects for consistency (Parmpreet Singh, 2026-01-23)
- Changed: Updated invoice router to properly convert service dict responses to Pydantic response models (Parmpreet Singh, 2026-01-23)
- Changed: Added status transition validation to invoice and purchase order update and approve methods (Parmpreet Singh, 2026-01-23)
- Changed: Archive functionality uses deleted flag with status set to "Archived" for invoices and purchase orders (Parmpreet Singh, 2026-01-23)

## 2026-01-20

- Fixed: Invoice API now returns job_uuid field by joining with obj_tp_job table, enabling proper navigation from invoices to job details (Parmpreet Singh, 2026-01-20)
- Changed: InvoiceResponse schema includes enriched job_uuid field from joined job table (Parmpreet Singh, 2026-01-20)
- Changed: list_invoices and get_invoice methods now perform LEFT JOIN with obj_tp_job to populate job_uuid (Parmpreet Singh, 2026-01-20)
- Fixed: PO-job relationship issue where jobid was numeric but job routes expect UUIDs (Parmpreet Singh, 2026-01-20)

All notable changes to the Invoice/Purchase Order Service API will be documented in this file.

## [Unreleased]

- Fixed: Added LEFT JOIN with obj_tp_job table in PurchaseOrderService list and get methods to enrich purchase order responses with job_id field, resolving issue where job IDs were not displayed in purchase orders list on frontend (Parmpreet Singh, 2026-01-20)
- Fixed: Updated PurchaseOrderResponse schema to include job_id as enriched field from joined obj_tp_job table (Parmpreet Singh, 2026-01-20)
- Fixed: Corrected database URL construction in database.py to properly extract password from SQLAlchemy URL object instead of string conversion which masked the password, resolving MySQL authentication failures (Parmpreet Singh, 2026-01-20)
- Fixed: Added field validator to convert MySQL bytes to int for is_internal field in PurchaseOrderBase schema, resolving Pydantic validation errors when reading purchase orders from database (Parmpreet Singh, 2026-01-20)
- Added: cryptography package to Pipfile for MySQL caching_sha2_password authentication method support (Parmpreet Singh, 2026-01-20)
- Added: ENVIRONMENT.md documentation with database and Redis configuration for Docker development (Parmpreet Singh, 2026-01-09)
- Added: Invoice/Purchase Order Service implementation with full CRUD operations (Parmpreet Singh, 2026-01-07)
- Added: Invoice models (Invoice, InvoiceGroup, InvoiceItem) with all database fields mapped (Parmpreet Singh, 2026-01-07)
- Added: Purchase Order models (PurchaseOrder, POMilestone) with all database fields mapped (Parmpreet Singh, 2026-01-07)
- Added: Invoice and Purchase Order enums for statuses and permissions (Parmpreet Singh, 2026-01-07)
- Added: Comprehensive Pydantic schemas for invoice and purchase order request/response validation (Parmpreet Singh, 2026-01-07)
- Added: InvoiceService with create, read, update, delete, approve, and list operations with filtering and pagination (Parmpreet Singh, 2026-01-07)
- Added: PurchaseOrderService with create, read, update, delete, approve, and list operations with filtering and pagination (Parmpreet Singh, 2026-01-07)
- Added: Authentication and authorization modules with role-based permissions (Parmpreet Singh, 2026-01-07)
- Added: API router with endpoints for invoices: GET /v1/invoices, GET /v1/invoices/{uuid}, POST /v1/invoices, PUT /v1/invoices/{uuid}, DELETE /v1/invoices/{uuid}, POST /v1/invoices/{uuid}/approve (Parmpreet Singh, 2026-01-07)
- Added: API router with endpoints for purchase orders: GET /v1/purchase-orders, GET /v1/purchase-orders/{uuid}, POST /v1/purchase-orders, PUT /v1/purchase-orders/{uuid}, DELETE /v1/purchase-orders/{uuid}, POST /v1/purchase-orders/{uuid}/approve (Parmpreet Singh, 2026-01-07)
- Changed: Updated database.py to include franchise and franchise_readonly database connections (Parmpreet Singh, 2026-01-07)
- Changed: Updated main.py to include invoice and purchase order routers (Parmpreet Singh, 2026-01-07)
- Changed: Updated main.py with proper service name and description for Invoice/Purchase Order Service API (Parmpreet Singh, 2026-01-07)
- Changed: Updated README.md with service-specific documentation and required environment variables (Parmpreet Singh, 2026-01-07)
- Added: Created RUNNING_THE_SERVICE.md with comprehensive setup and running instructions (Parmpreet Singh, 2026-01-07)
- Fixed: Made Elastic APM import optional to prevent ModuleNotFoundError when dependencies aren't installed (Parmpreet Singh, 2026-01-07)
- Added: Created TROUBLESHOOTING.md with solutions for common issues (Parmpreet Singh, 2026-01-07)
- Fixed: Updated health check to only verify franchise database connection, making sitemanager database optional (Parmpreet Singh, 2026-01-07)
- Fixed: Removed withholding_tax column from Invoice and InvoiceGroup models as it doesn't exist in the actual database table (Parmpreet Singh, 2026-01-07)
- Added: Created DATABASE_CONNECTION_FIX.md with solutions for database access issues without using GRANT statements (Parmpreet Singh, 2026-01-07)
- Added: Created DOCKER_MYSQL_FIX.md with solution for Docker intercepting MySQL connections on port 3306 (Parmpreet Singh, 2026-01-07)
- Added: Created DOCKER_PORT_3306_FIX.md with detailed solutions for Docker intercepting port 3306 without requiring GRANT statements (Parmpreet Singh, 2026-01-07)
- Added: Created MYSQL_IN_DOCKER_FIX.md with solutions for connecting to MySQL running in Docker without using GRANT statements (Parmpreet Singh, 2026-01-07)
- Added: Created MYSQL_DOCKER_TROUBLESHOOTING.md with troubleshooting steps for MySQL access denied errors in Docker containers (Parmpreet Singh, 2026-01-07)
- Fixed: Resolved MySQL access denied errors by resetting root password using --skip-grant-tables and updating .env with correct password (Parmpreet Singh, 2026-01-08)

