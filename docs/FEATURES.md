# Invoice/Purchase Order/Sales Order Service Features

**Last Updated**: 2026-01-23

## Overview

The Invoice/Purchase Order Service API provides comprehensive financial management capabilities for the Straker translation platform. This service manages invoices, purchase orders, sales orders, and their associated line items, groups, milestones, and disbursements.

## Core Features

### 1. Invoice Management

**Endpoints:**
- `GET /v1/invoices` - List invoices with filtering and pagination
- `GET /v1/invoices/{uuid}` - Get invoice by UUID
- `POST /v1/invoices` - Create new invoice
- `PUT /v1/invoices/{uuid}` - Update invoice
- `DELETE /v1/invoices/{uuid}` - Delete invoice (soft delete)
- `POST /v1/invoices/{uuid}/approve` - Approve invoice
- `POST /v1/invoices/{uuid}/archive` - Archive invoice
- `POST /v1/invoices/{uuid}/restore` - Restore archived invoice

**Features:**
- Full CRUD operations
- Status workflow validation
- Archive/restore functionality
- Approval workflow
- Filtering by status, job_id, client_name, dates, currency
- Pagination support
- Enriched responses with job_uuid from joined obj_tp_job table

**Status Values:**
- Draft, Pending, Sent, Paid, Overdue, Cancelled, Refunded

**Status Transitions:**
- Draft → Pending → Sent → Paid
- Draft → Pending → Sent → Overdue → Paid
- Draft → Pending → Sent → Cancelled (terminal)
- Paid → Refunded (terminal)

### 2. Invoice Line Items

**Endpoints:**
- `GET /v1/invoices/{uuid}/items` - List invoice line items
- `POST /v1/invoices/{uuid}/items` - Add line item to invoice
- `GET /v1/invoices/{uuid}/items/{item_uuid}` - Get invoice line item
- `PUT /v1/invoices/{uuid}/items/{item_uuid}` - Update invoice line item
- `DELETE /v1/invoices/{uuid}/items/{item_uuid}` - Remove line item from invoice

**Features:**
- Support for language pairs, additional items, and other item types
- Item-level currency and pricing
- Automatic sorting (target_lang null items first, then by item_type)

### 3. Invoice Groups

**Endpoints:**
- `GET /v1/invoice-groups` - List invoice groups with filtering
- `GET /v1/invoice-groups/{uuid}` - Get invoice group with invoices
- `POST /v1/invoice-groups` - Create new invoice group
- `PUT /v1/invoice-groups/{uuid}` - Update invoice group
- `DELETE /v1/invoice-groups/{uuid}` - Delete invoice group
- `POST /v1/invoice-groups/{uuid}/add-invoice` - Add invoice to group
- `POST /v1/invoice-groups/{uuid}/remove-invoice` - Remove invoice from group

**Features:**
- Periodic/consolidated invoicing
- Multiple display options (include invoices, job titles, word rates, etc.)
- Language-based ordering support
- Group-level financial tracking

### 4. Purchase Order Management

**Endpoints:**
- `GET /v1/purchase-orders` - List purchase orders with filtering
- `GET /v1/purchase-orders/{uuid}` - Get purchase order by UUID
- `POST /v1/purchase-orders` - Create new purchase order
- `PUT /v1/purchase-orders/{uuid}` - Update purchase order
- `DELETE /v1/purchase-orders/{uuid}` - Delete purchase order (soft delete)
- `POST /v1/purchase-orders/{uuid}/approve` - Approve purchase order for payment
- `POST /v1/purchase-orders/{uuid}/archive` - Archive purchase order
- `POST /v1/purchase-orders/{uuid}/restore` - Restore archived purchase order
- `POST /v1/purchase-orders/batch-approve` - Approve multiple purchase orders
- `POST /v1/purchase-orders/batch-delete` - Delete multiple purchase orders

**Features:**
- Full CRUD operations
- Approval workflow with auto-approval thresholds
- Batch operations for efficiency
- Archive/restore functionality
- Filtering by status, job_id, translator_id, project_manager_id, dates, currency, approval status
- Enriched responses with job_id from joined obj_tp_job table
- Support for internal POs, disputed POs, expired POs

**Status Values:**
- Pending, Accepted, Declined, In Progress, Completed, Approved, Paid, Cancelled, Expired, Disputed

**Status Transitions:**
- Pending → Accepted → In Progress → Completed → Approved → Paid
- Pending → Declined (terminal)
- Pending → Cancelled (terminal)
- Disputed → Approved or Cancelled

### 5. Purchase Order Milestones

**Endpoints:**
- `GET /v1/purchase-orders/{uuid}/milestones` - List PO milestones
- `POST /v1/purchase-orders/{uuid}/milestones` - Record PO milestone
- `PUT /v1/purchase-orders/{uuid}/milestones/{milestone_uuid}` - Update PO milestone

**Features:**
- Track completion percentages (25%, 50%, 75%, 100%)
- Milestone confirmation tracking
- Notes and remote IP logging
- Automatic ordering by milestone percentage

### 6. Purchase Order Disbursements

**Endpoints:**
- `GET /v1/purchase-orders/{uuid}/disbursements` - List PO disbursement items
- `POST /v1/purchase-orders/{uuid}/disbursements` - Add disbursement item
- `PUT /v1/purchase-orders/{uuid}/disbursements/{item_uuid}` - Update disbursement item
- `DELETE /v1/purchase-orders/{uuid}/disbursements/{item_uuid}` - Delete disbursement item

**Features:**
- Support for DTP and other disbursement types
- Item type information tracking
- Unit-based pricing (no_of_units × rate_per_unit = total_cost)
- Automatic sorting by item_type

### 7. Sales Order Management

**Endpoints:**
- `GET /v1/sales-orders` - List sales orders with filtering and pagination
- `GET /v1/sales-orders/{uuid}` - Get sales order by UUID
- `POST /v1/sales-orders` - Create new sales order
- `PUT /v1/sales-orders/{uuid}` - Update sales order
- `DELETE /v1/sales-orders/{uuid}` - Delete sales order (soft delete)
- `POST /v1/sales-orders/{uuid}/transform-to-invoice` - Transform sales order to invoice
- `POST /v1/sales-orders/{uuid}/cancel` - Cancel sales order

**Features:**
- Sales Orders are stored as invoices with `invoice_type = 'Pro Forma'` or `'Sales Order'`
- Transform to regular invoice functionality
- Cancel with reason tracking
- Full CRUD operations
- Filtering by status, job_id, group_id, dates, currency

**Status Values:**
- Draft, Pending, Sent, Cancelled, Transformed

## Arguments Required

### Creating a Purchase Order

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| tp_job | string(36) | Yes | Job UUID |
| translatorid | string(36) | Yes | Translator UUID |
| amount | decimal | Yes | PO amount |
| currency | string | Yes | Currency code |
| po_type | string | No | Translation, DTP, Disbursement |
| order_date | datetime | No | Defaults to now |
| date_due | datetime | No | Due date |
| order_notes | text | No | Notes |
| target_lang | string | No | Target language |
| status | string | No | Defaults to "Pending" |

### Creating an Invoice

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| jobid | int | Yes | Job ID |
| amount | decimal | Yes | Total amount |
| currency | string | Yes | Currency code |
| invoice_type | string | No | Tax Invoice, Deposit, etc. |
| status | string | No | Draft, Pending, etc. (defaults to "Draft") |
| client_name | string | No | Client name |
| inv_date | datetime | No | Invoice date |
| due_date | datetime | No | Due date |

### Creating a Sales Order

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| jobid | int | Yes | Job ID |
| amount_nett | decimal | Yes | Net amount |
| currency | string | Yes | Currency code |
| invoice_type | string | Yes | Must be 'Pro Forma' or 'Sales Order' |
| status | string | No | Defaults to "Draft" |

### Creating an Invoice Line Item

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| invoice_uuid | string(36) | Yes | Invoice UUID |
| item_type | string | Yes | language_pair, additional_item, etc. |
| amount_nett | decimal | Yes | Item net amount |
| currency | string | Yes | Currency code |
| source_lang | string | No | Source language |
| target_lang | string | No | Target language |
| unit_price | decimal | No | Unit price |

### Creating an Invoice Group

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| companyid | string(36) | Yes | Company/Group UUID |
| currency | string | Yes | Currency code |
| invoice_date | datetime | Yes | Invoice date |
| status | string | No | Defaults to "Draft" |
| due_date | datetime | No | Due date |

### Creating a PO Milestone

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| tp_purchaseorder | string(36) | Yes | Purchase Order UUID |
| milestone | int | Yes | Milestone percentage (1-100) |
| notes | string | No | Milestone notes |
| confirmed | int | No | Confirmation status |

### Creating a PO Disbursement Item

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| po_uuid | string(36) | Yes | Purchase Order UUID |
| item_type | string | Yes | Item type (DTP, etc.) |
| item_type_info | string | Yes | Item type information |
| no_of_units | int | Yes | Number of units |
| rate_per_unit | decimal | Yes | Rate per unit |
| total_cost | decimal | Yes | Total cost |

## Status Workflow

The service enforces valid status transitions to maintain data integrity:

**Invoice Status Flow:**
```
Draft → Pending → Sent → Paid
                    ↓
                 Overdue → Paid
                    ↓
                 Cancelled (terminal)
```

**Purchase Order Status Flow:**
```
Pending → Accepted → In Progress → Completed → Approved → Paid
    ↓         ↓
Declined   Cancelled (both terminal)
```

Invalid transitions will raise `InvalidStatusTransitionError` with details about allowed transitions.

## Permissions

The service implements role-based access control:

**Admin & Finance Roles:**
- Full access to all operations

**Team Lead:**
- Create, read, update, approve invoices and purchase orders
- Transform and cancel sales orders
- Manage line items, groups, milestones, disbursements

**Team Member:**
- Read access
- Limited update access (specific fields only)

## Testing

Comprehensive test coverage includes:

**Unit Tests:**
- Service layer tests for all CRUD operations
- Status workflow validation tests
- Permission/RBAC tests
- Edge cases and error handling

**Integration Tests:**
- Full API endpoint tests
- Database interaction tests
- Cross-service validation
- Error handling scenarios

Run tests with:
```bash
pytest tests/ -v
```

## Database Schema

**Primary Tables:**
- `franchise.obj_tp_job_invoice` - Invoices and Sales Orders
- `franchise.obj_tp_job_invoice_item` - Invoice line items
- `franchise.obj_tp_job_invoice_group` - Invoice groups
- `franchise.obj_tp_purchaseorder` - Purchase orders
- `franchise.obj_tp_po_milestones` - PO milestones
- `franchise.obj_tp_po_disbursements_item` - PO disbursement items

**Key Relationships:**
- Invoices → Jobs (via `jobid`)
- Invoices → Invoice Groups (via `invoice_groupid`)
- Purchase Orders → Jobs (via `tp_job`)
- Sales Orders are stored as invoices with `invoice_type = 'Pro Forma'` or `'Sales Order'`
