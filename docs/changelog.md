# Changelog

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

