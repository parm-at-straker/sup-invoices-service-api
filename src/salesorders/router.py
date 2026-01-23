"""Sales Order API routers."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..pagination import paginate, validate_pagination
from ..invoices.auth import get_current_user_role
from ..invoices.dependencies import get_franchise_db
from .dependencies import get_sales_order_service
from .enums import SalesOrderPermission
from .permissions import require_sales_order_permission
from .schemas import (
    SalesOrderCreate,
    SalesOrderDetailResponse,
    SalesOrderFilterParams,
    SalesOrderListResponse,
    SalesOrderUpdate,
    TransformToInvoiceRequest,
    CancelSalesOrderRequest,
)
from .service import (
    SalesOrderNotFoundError,
    SalesOrderService,
)


router = APIRouter()


@router.get("/sales-orders", response_model=SalesOrderListResponse)
async def list_sales_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    group_id: Optional[str] = Query(None, description="Filter by group UUID"),
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
    so_service: SalesOrderService = Depends(get_sales_order_service),
    user: dict = Depends(get_current_user_role),
):
    """List sales orders with filtering and pagination.

    Args:
        status: Filter by status
        job_id: Filter by job ID
        group_id: Filter by group UUID
        inv_date_from: Filter by invoice date from
        inv_date_to: Filter by invoice date to
        due_date_from: Filter by due date from
        due_date_to: Filter by due date to
        currency: Filter by currency
        page: Page number
        page_size: Items per page
        sort_by: Sort field
        sort_order: Sort order (asc/desc)
        so_service: Sales order service instance
        user: Current user

    Returns:
        Paginated list of sales orders
    """
    # Check permission
    require_sales_order_permission(user["role"], SalesOrderPermission.READ)

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
    filters = SalesOrderFilterParams(
        status=status,
        job_id=job_id,
        group_id=group_id,
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

    # Get sales orders
    sales_orders, total = await so_service.list_sales_orders(filters)

    # Convert dicts to SalesOrderResponse objects
    from .schemas import SalesOrderResponse

    so_objects = [SalesOrderResponse.model_validate(so) for so in sales_orders]

    return SalesOrderListResponse(
        data=so_objects,
        pagination=paginate(pagination, total),
    )


@router.get("/sales-orders/{so_uuid}", response_model=SalesOrderDetailResponse)
async def get_sales_order(
    so_uuid: str,
    so_service: SalesOrderService = Depends(get_sales_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Get a sales order by UUID.

    Args:
        so_uuid: Sales order UUID
        so_service: Sales order service instance
        user: Current user

    Returns:
        Sales order details

    Raises:
        HTTPException: If sales order not found
    """
    # Check permission
    require_sales_order_permission(user["role"], SalesOrderPermission.READ)

    try:
        so_dict = await so_service.get_sales_order_or_404(so_uuid)

        # Convert dict to SalesOrderResponse object
        from .schemas import SalesOrderResponse

        so = SalesOrderResponse.model_validate(so_dict)
        return SalesOrderDetailResponse(data=so)
    except SalesOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/sales-orders",
    response_model=SalesOrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sales_order(
    so_data: SalesOrderCreate,
    so_service: SalesOrderService = Depends(get_sales_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Create a new sales order.

    Args:
        so_data: Sales order creation data
        so_service: Sales order service instance
        user: Current user

    Returns:
        Created sales order

    Raises:
        HTTPException: If creation fails
    """
    # Check permission
    require_sales_order_permission(user["role"], SalesOrderPermission.CREATE)

    try:
        so = await so_service.create_sales_order(so_data, user["user_id"])
        from .schemas import SalesOrderResponse

        so_obj = SalesOrderResponse.model_validate(so)
        return SalesOrderDetailResponse(data=so_obj)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create sales order: {str(e)}",
        ) from e


@router.put("/sales-orders/{so_uuid}", response_model=SalesOrderDetailResponse)
async def update_sales_order(
    so_uuid: str,
    so_data: SalesOrderUpdate,
    so_service: SalesOrderService = Depends(get_sales_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Update a sales order.

    Args:
        so_uuid: Sales order UUID
        so_data: Sales order update data
        so_service: Sales order service instance
        user: Current user

    Returns:
        Updated sales order

    Raises:
        HTTPException: If sales order not found or update fails
    """
    # Check permission
    require_sales_order_permission(user["role"], SalesOrderPermission.UPDATE)

    try:
        so = await so_service.update_sales_order(so_uuid, so_data, user["user_id"])
        from .schemas import SalesOrderResponse

        so_obj = SalesOrderResponse.model_validate(so)
        return SalesOrderDetailResponse(data=so_obj)
    except SalesOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update sales order: {str(e)}",
        ) from e


@router.delete("/sales-orders/{so_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sales_order(
    so_uuid: str,
    so_service: SalesOrderService = Depends(get_sales_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Delete a sales order (soft delete).

    Args:
        so_uuid: Sales order UUID
        so_service: Sales order service instance
        user: Current user

    Raises:
        HTTPException: If sales order not found or deletion fails
    """
    # Check permission
    require_sales_order_permission(user["role"], SalesOrderPermission.DELETE)

    try:
        await so_service.delete_sales_order(so_uuid, user["user_id"])
    except SalesOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete sales order: {str(e)}",
        ) from e


@router.post(
    "/sales-orders/{so_uuid}/transform-to-invoice",
    response_model=SalesOrderDetailResponse,
)
async def transform_sales_order_to_invoice(
    so_uuid: str,
    transform_data: TransformToInvoiceRequest,
    so_service: SalesOrderService = Depends(get_sales_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Transform a sales order to an invoice.

    Args:
        so_uuid: Sales order UUID
        transform_data: Transformation data
        so_service: Sales order service instance
        user: Current user

    Returns:
        Transformed invoice (now a regular invoice)

    Raises:
        HTTPException: If sales order not found or transformation fails
    """
    # Check permission
    require_sales_order_permission(user["role"], SalesOrderPermission.TRANSFORM)

    try:
        invoice = await so_service.transform_to_invoice(
            so_uuid, transform_data, user["user_id"]
        )
        from .schemas import SalesOrderResponse

        invoice_obj = SalesOrderResponse.model_validate(invoice)
        return SalesOrderDetailResponse(data=invoice_obj)
    except SalesOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to transform sales order: {str(e)}",
        ) from e


@router.post(
    "/sales-orders/{so_uuid}/cancel",
    response_model=SalesOrderDetailResponse,
)
async def cancel_sales_order(
    so_uuid: str,
    cancel_data: CancelSalesOrderRequest,
    so_service: SalesOrderService = Depends(get_sales_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Cancel a sales order.

    Args:
        so_uuid: Sales order UUID
        cancel_data: Cancellation data
        so_service: Sales order service instance
        user: Current user

    Returns:
        Cancelled sales order

    Raises:
        HTTPException: If sales order not found or cancellation fails
    """
    # Check permission
    require_sales_order_permission(user["role"], SalesOrderPermission.CANCEL)

    try:
        so = await so_service.cancel_sales_order(
            so_uuid, cancel_data.reason, user["user_id"]
        )
        from .schemas import SalesOrderResponse

        so_obj = SalesOrderResponse.model_validate(so)
        return SalesOrderDetailResponse(data=so_obj)
    except SalesOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel sales order: {str(e)}",
        ) from e
