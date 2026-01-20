"""Invoice and Purchase Order API routers."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..pagination import paginate, validate_pagination
from .auth import get_current_user_role
from .dependencies import get_invoice_service, get_purchase_order_service
from .enums import InvoicePermission, POPermission
from .permissions import require_invoice_permission, require_po_permission
from .schemas import (
    InvoiceCreate,
    InvoiceDetailResponse,
    InvoiceFilterParams,
    InvoiceListResponse,
    InvoiceUpdate,
    PurchaseOrderCreate,
    PurchaseOrderDetailResponse,
    PurchaseOrderFilterParams,
    PurchaseOrderListResponse,
    PurchaseOrderUpdate,
)
from .service import (
    InvoiceNotFoundError,
    InvoiceService,
    PurchaseOrderNotFoundError,
    PurchaseOrderService,
)


router = APIRouter()

# Invoice Endpoints


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    status: Optional[str] = Query(None, description="Filter by status"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    invoice_group_id: Optional[int] = Query(None, description="Filter by invoice group ID"),
    client_name: Optional[str] = Query(None, description="Filter by client name"),
    inv_date_from: Optional[str] = Query(
        None, description="Filter by invoice date from (ISO format)"
    ),
    inv_date_to: Optional[str] = Query(None, description="Filter by invoice date to (ISO format)"),
    due_date_from: Optional[str] = Query(None, description="Filter by due date from (ISO format)"),
    due_date_to: Optional[str] = Query(None, description="Filter by due date to (ISO format)"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query("inv_date", description="Sort field"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """List invoices with filtering and pagination.

    Args:
        status: Filter by status
        job_id: Filter by job ID
        invoice_group_id: Filter by invoice group ID
        client_name: Filter by client name
        inv_date_from: Filter by invoice date from
        inv_date_to: Filter by invoice date to
        due_date_from: Filter by due date from
        due_date_to: Filter by due date to
        currency: Filter by currency
        page: Page number
        page_size: Items per page
        sort_by: Sort field
        sort_order: Sort order (asc/desc)
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Paginated list of invoices
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.READ)

    # Parse date strings if provided
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string to datetime."""
        if not date_str:
            return None
        try:
            if date_str.endswith("Z"):
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return datetime.fromisoformat(date_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format: {date_str}. Use ISO 8601 format.",
            )

    inv_date_from_dt = parse_date(inv_date_from)
    inv_date_to_dt = parse_date(inv_date_to)
    due_date_from_dt = parse_date(due_date_from)
    due_date_to_dt = parse_date(due_date_to)

    # Create filter params
    filters = InvoiceFilterParams(
        status=status,
        job_id=job_id,
        invoice_group_id=invoice_group_id,
        client_name=client_name,
        inv_date_from=inv_date_from_dt,
        inv_date_to=inv_date_to_dt,
        due_date_from=due_date_from_dt,
        due_date_to=due_date_to_dt,
        currency=currency,
        page=page,
        page_size=page_size,
        sort_by=sort_by or "inv_date",
        sort_order=sort_order or "desc",
    )

    # Validate pagination
    pagination = validate_pagination(page, page_size)

    # Get invoices
    invoices, total = await invoice_service.list_invoices(filters)

    # Convert dicts to InvoiceResponse objects
    from .schemas import InvoiceResponse

    invoice_objects = [InvoiceResponse.model_validate(inv) for inv in invoices]

    return InvoiceListResponse(
        data=invoice_objects,
        pagination=paginate(pagination, total),
    )


@router.get("/invoices/{invoice_uuid}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_uuid: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Get an invoice by UUID.

    Args:
        invoice_uuid: Invoice UUID
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Invoice details

    Raises:
        HTTPException: If invoice not found
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.READ)

    try:
        invoice_dict = await invoice_service.get_invoice(invoice_uuid)
        if not invoice_dict:
            raise InvoiceNotFoundError(f"Invoice with UUID {invoice_uuid} not found")

        # Convert dict to InvoiceResponse object
        from .schemas import InvoiceResponse

        invoice = InvoiceResponse.model_validate(invoice_dict)
        return InvoiceDetailResponse(data=invoice)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/invoices", response_model=InvoiceDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Create a new invoice.

    Args:
        invoice_data: Invoice creation data
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Created invoice

    Raises:
        HTTPException: If creation fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.CREATE)

    try:
        invoice = await invoice_service.create_invoice(invoice_data, user["user_id"])
        return InvoiceDetailResponse(data=invoice)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create invoice: {str(e)}",
        ) from e


@router.put("/invoices/{invoice_uuid}", response_model=InvoiceDetailResponse)
async def update_invoice(
    invoice_uuid: str,
    invoice_data: InvoiceUpdate,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Update an invoice.

    Args:
        invoice_uuid: Invoice UUID
        invoice_data: Invoice update data
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Updated invoice

    Raises:
        HTTPException: If invoice not found or update fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.UPDATE)

    try:
        invoice = await invoice_service.update_invoice(invoice_uuid, invoice_data, user["user_id"])
        return InvoiceDetailResponse(data=invoice)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update invoice: {str(e)}",
        ) from e


@router.delete("/invoices/{invoice_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_uuid: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Delete an invoice (soft delete).

    Args:
        invoice_uuid: Invoice UUID
        invoice_service: Invoice service instance
        user: Current user

    Raises:
        HTTPException: If invoice not found or deletion fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.DELETE)

    try:
        await invoice_service.delete_invoice(invoice_uuid, user["user_id"])
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete invoice: {str(e)}",
        ) from e


@router.post("/invoices/{invoice_uuid}/approve", response_model=InvoiceDetailResponse)
async def approve_invoice(
    invoice_uuid: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Approve an invoice.

    Args:
        invoice_uuid: Invoice UUID
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Approved invoice

    Raises:
        HTTPException: If invoice not found or approval fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.APPROVE)

    try:
        invoice = await invoice_service.approve_invoice(invoice_uuid, user["user_id"])
        return InvoiceDetailResponse(data=invoice)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to approve invoice: {str(e)}",
        ) from e


# Purchase Order Endpoints


@router.get("/purchase-orders", response_model=PurchaseOrderListResponse)
async def list_purchase_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    job_id: Optional[str] = Query(None, description="Filter by job UUID"),
    translator_id: Optional[str] = Query(None, description="Filter by translator UUID"),
    project_manager_id: Optional[str] = Query(None, description="Filter by project manager UUID"),
    order_date_from: Optional[str] = Query(
        None, description="Filter by order date from (ISO format)"
    ),
    order_date_to: Optional[str] = Query(None, description="Filter by order date to (ISO format)"),
    date_due_from: Optional[str] = Query(None, description="Filter by due date from (ISO format)"),
    date_due_to: Optional[str] = Query(None, description="Filter by due date to (ISO format)"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    approved_for_payment: Optional[bool] = Query(
        None, description="Filter by approved for payment"
    ),
    accepted: Optional[bool] = Query(None, description="Filter by accepted status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query("order_date", description="Sort field"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """List purchase orders with filtering and pagination.

    Args:
        status: Filter by status
        job_id: Filter by job UUID
        translator_id: Filter by translator UUID
        project_manager_id: Filter by project manager UUID
        order_date_from: Filter by order date from
        order_date_to: Filter by order date to
        date_due_from: Filter by due date from
        date_due_to: Filter by due date to
        currency: Filter by currency
        approved_for_payment: Filter by approved for payment
        accepted: Filter by accepted status
        page: Page number
        page_size: Items per page
        sort_by: Sort field
        sort_order: Sort order (asc/desc)
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Paginated list of purchase orders
    """
    # Check permission
    require_po_permission(user["role"], POPermission.READ)

    # Parse date strings if provided
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string to datetime."""
        if not date_str:
            return None
        try:
            if date_str.endswith("Z"):
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return datetime.fromisoformat(date_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format: {date_str}. Use ISO 8601 format.",
            )

    order_date_from_dt = parse_date(order_date_from)
    order_date_to_dt = parse_date(order_date_to)
    date_due_from_dt = parse_date(date_due_from)
    date_due_to_dt = parse_date(date_due_to)

    # Create filter params
    filters = PurchaseOrderFilterParams(
        status=status,
        job_id=job_id,
        translator_id=translator_id,
        project_manager_id=project_manager_id,
        order_date_from=order_date_from_dt,
        order_date_to=order_date_to_dt,
        date_due_from=date_due_from_dt,
        date_due_to=date_due_to_dt,
        currency=currency,
        approved_for_payment=approved_for_payment,
        accepted=accepted,
        page=page,
        page_size=page_size,
        sort_by=sort_by or "order_date",
        sort_order=sort_order or "desc",
    )

    # Validate pagination
    pagination = validate_pagination(page, page_size)

    # Get purchase orders
    pos, total = await po_service.list_purchase_orders(filters)

    return PurchaseOrderListResponse(
        data=pos,
        pagination=paginate(pagination, total),
    )


@router.get("/purchase-orders/{po_uuid}", response_model=PurchaseOrderDetailResponse)
async def get_purchase_order(
    po_uuid: str,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Get a purchase order by UUID.

    Args:
        po_uuid: Purchase order UUID
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Purchase order details

    Raises:
        HTTPException: If purchase order not found
    """
    # Check permission
    require_po_permission(user["role"], POPermission.READ)

    try:
        po = await po_service.get_purchase_order_or_404(po_uuid)
        return PurchaseOrderDetailResponse(data=po)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/purchase-orders",
    response_model=PurchaseOrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Create a new purchase order.

    Args:
        po_data: Purchase order creation data
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Created purchase order

    Raises:
        HTTPException: If creation fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.CREATE)

    try:
        po = await po_service.create_purchase_order(po_data, user["user_id"])
        return PurchaseOrderDetailResponse(data=po)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create purchase order: {str(e)}",
        ) from e


@router.put("/purchase-orders/{po_uuid}", response_model=PurchaseOrderDetailResponse)
async def update_purchase_order(
    po_uuid: str,
    po_data: PurchaseOrderUpdate,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Update a purchase order.

    Args:
        po_uuid: Purchase order UUID
        po_data: Purchase order update data
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Updated purchase order

    Raises:
        HTTPException: If purchase order not found or update fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.UPDATE)

    try:
        po = await po_service.update_purchase_order(po_uuid, po_data, user["user_id"])
        return PurchaseOrderDetailResponse(data=po)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update purchase order: {str(e)}",
        ) from e


@router.delete("/purchase-orders/{po_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(
    po_uuid: str,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Delete a purchase order (soft delete).

    Args:
        po_uuid: Purchase order UUID
        po_service: Purchase order service instance
        user: Current user

    Raises:
        HTTPException: If purchase order not found or deletion fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.DELETE)

    try:
        await po_service.delete_purchase_order(po_uuid, user["user_id"])
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete purchase order: {str(e)}",
        ) from e


@router.post("/purchase-orders/{po_uuid}/approve", response_model=PurchaseOrderDetailResponse)
async def approve_purchase_order(
    po_uuid: str,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Approve a purchase order for payment.

    Args:
        po_uuid: Purchase order UUID
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Approved purchase order

    Raises:
        HTTPException: If purchase order not found or approval fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.APPROVE)

    try:
        po = await po_service.approve_purchase_order(po_uuid, user["user_id"])
        return PurchaseOrderDetailResponse(data=po)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to approve purchase order: {str(e)}",
        ) from e
