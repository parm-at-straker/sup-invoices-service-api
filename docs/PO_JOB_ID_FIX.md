# Purchase Order Job ID Fix

## Issue

The Purchase Orders page in the verify-hub-ui was displaying "N/A" for all Job IDs in the purchase orders list. The frontend component was configured to display `job_id` but the API was not returning this field.

## Root Cause

The `job_id` field is documented in the TypeScript types as an "enriched field (from joins)", but the `PurchaseOrderService.list_purchase_orders()` method was only querying the `obj_tp_purchaseorder` table without joining to the `obj_tp_job` table to retrieve the job's integer ID.

The `PurchaseOrder` model stores `tp_job` which is the job's UUID, but the frontend needs `job_id` which is the job's integer ID field from the `obj_tp_job` table.

## Solution

### Changes Made

1. **Updated `PurchaseOrderService.list_purchase_orders()`** (`src/invoices/service.py`)
   - Added LEFT JOIN with `obj_tp_job` table to retrieve `job.id` 
   - Modified query to return dictionaries containing enriched `job_id` field
   - Updated return type from `List[PurchaseOrder]` to `List[dict]`

2. **Updated `PurchaseOrderService.get_purchase_order()`** (`src/invoices/service.py`)
   - Added LEFT JOIN with `obj_tp_job` table
   - Modified to return dictionary with `job_id` field instead of model object
   - Updated return type from `Optional[PurchaseOrder]` to `Optional[dict]`

3. **Updated `PurchaseOrderService.get_purchase_order_or_404()`** (`src/invoices/service.py`)
   - Updated return type from `PurchaseOrder` to `dict`

4. **Updated `PurchaseOrderService.create_purchase_order()`** (`src/invoices/service.py`)
   - Modified to return enriched dict by calling `get_purchase_order()` after creation
   - Updated return type from `PurchaseOrder` to `dict`

5. **Updated `PurchaseOrderService.update_purchase_order()`** (`src/invoices/service.py`)
   - Modified to fetch model directly for updates (not enriched dict)
   - Returns enriched dict by calling `get_purchase_order()` after update
   - Updated return type from `PurchaseOrder` to `dict`

6. **Updated `PurchaseOrderService.approve_purchase_order()`** (`src/invoices/service.py`)
   - Modified to fetch model directly for updates (not enriched dict)
   - Returns enriched dict by calling `get_purchase_order()` after approval
   - Updated return type from `PurchaseOrder` to `dict`

7. **Updated `PurchaseOrderService.delete_purchase_order()`** (`src/invoices/service.py`)
   - Modified to fetch model directly for deletion (not enriched dict)

8. **Updated `PurchaseOrderResponse` schema** (`src/invoices/schemas.py`)
   - Added `job_id: Optional[int]` field with description indicating it's from joined table

## Technical Details

### SQL Join Implementation

The fix uses SQLAlchemy's Table construct to define the `obj_tp_job` table dynamically and performs a LEFT JOIN:

```python
from sqlalchemy import Table, MetaData, Column, Integer, String

metadata = MetaData(schema="franchise")
job_table = Table(
    "obj_tp_job",
    metadata,
    Column("obj_uuid", String(36), primary_key=True),
    Column("id", Integer),
    autoload_with=self.db.get_bind(),
)

stmt = (
    select(
        PurchaseOrder,
        job_table.c.id.label("job_id"),
    )
    .outerjoin(job_table, PurchaseOrder.tp_job == job_table.c.obj_uuid)
    .where(PurchaseOrder.is_deleted != True)
)
```

### Data Transformation

After executing the query, results are transformed from SQLAlchemy Row objects to dictionaries:

```python
for row in rows:
    po = row[0]  # PurchaseOrder model
    job_id = row[1]  # job.id from join
    
    po_dict = {
        column.name: getattr(po, column.name)
        for column in PurchaseOrder.__table__.columns
    }
    po_dict["job_id"] = job_id
    pos_with_job_id.append(po_dict)
```

## Testing

After deploying these changes, the Purchase Orders page should:
1. Display actual job IDs instead of "N/A"
2. Allow clicking on job IDs to navigate to the job detail page
3. Maintain all existing filtering and sorting functionality

## Files Changed

- `src/invoices/service.py` - Updated PurchaseOrderService methods
- `src/invoices/schemas.py` - Added job_id to PurchaseOrderResponse
- `docs/changelog.md` - Documented the fix

## Date

2026-01-20

## Author

Parmpreet Singh
