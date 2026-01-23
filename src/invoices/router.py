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
    InvoiceItemCreate,
    InvoiceItemDetailResponse,
    InvoiceItemListResponse,
    InvoiceItemUpdate,
    InvoiceGroupCreate,
    InvoiceGroupDetailResponse,
    InvoiceGroupFilterParams,
    InvoiceGroupListResponse,
    InvoiceGroupUpdate,
    AddInvoiceToGroupRequest,
    RemoveInvoiceFromGroupRequest,
    POMilestoneCreate,
    POMilestoneResponse,
    POMilestoneUpdate,
    PODisbursementItemCreate,
    PODisbursementItemDetailResponse,
    PODisbursementItemListResponse,
    PODisbursementItemUpdate,
    BatchPOApproveRequest,
    BatchPODeleteRequest,
    BatchOperationResponse,
    PurchaseOrderCreate,
    PurchaseOrderDetailResponse,
    PurchaseOrderFilterParams,
    PurchaseOrderListResponse,
    PurchaseOrderUpdate,
)
from .service import (
    InvoiceGroupNotFoundError,
    InvoiceNotFoundError,
    InvoiceService,
    PurchaseOrderNotFoundError,
    PurchaseOrderService,
)
from .workflow import InvalidStatusTransitionError


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
        invoice_dict = await invoice_service.create_invoice(invoice_data, user["user_id"])
        from .schemas import InvoiceResponse

        invoice = InvoiceResponse.model_validate(invoice_dict)
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
        invoice_dict = await invoice_service.update_invoice(invoice_uuid, invoice_data, user["user_id"])
        from .schemas import InvoiceResponse

        invoice = InvoiceResponse.model_validate(invoice_dict)
        return InvoiceDetailResponse(data=invoice)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
        invoice_dict = await invoice_service.approve_invoice(invoice_uuid, user["user_id"])
        from .schemas import InvoiceResponse

        invoice = InvoiceResponse.model_validate(invoice_dict)
        return InvoiceDetailResponse(data=invoice)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to approve invoice: {str(e)}",
        ) from e


# Invoice Item Endpoints


@router.get("/invoices/{invoice_uuid}/items", response_model=InvoiceItemListResponse)
async def list_invoice_items(
    invoice_uuid: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """List all items for an invoice.

    Args:
        invoice_uuid: Invoice UUID
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        List of invoice items

    Raises:
        HTTPException: If invoice not found
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.READ)

    try:
        # Verify invoice exists
        await invoice_service.get_invoice_or_404(invoice_uuid)

        items = await invoice_service.list_invoice_items(invoice_uuid)
        from .schemas import InvoiceItemResponse

        item_objects = [InvoiceItemResponse.model_validate(item) for item in items]
        return InvoiceItemListResponse(data=item_objects)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/invoices/{invoice_uuid}/items",
    response_model=InvoiceItemDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invoice_item(
    invoice_uuid: str,
    item_data: InvoiceItemCreate,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Create a new invoice item.

    Args:
        invoice_uuid: Invoice UUID
        item_data: Invoice item creation data
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Created invoice item

    Raises:
        HTTPException: If creation fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.UPDATE)

    try:
        item = await invoice_service.create_invoice_item(
            invoice_uuid, item_data, user["user_id"]
        )
        from .schemas import InvoiceItemResponse

        item_obj = InvoiceItemResponse.model_validate(item)
        return InvoiceItemDetailResponse(data=item_obj)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create invoice item: {str(e)}",
        ) from e


@router.get(
    "/invoices/{invoice_uuid}/items/{item_uuid}",
    response_model=InvoiceItemDetailResponse,
)
async def get_invoice_item(
    invoice_uuid: str,
    item_uuid: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Get an invoice item by UUID.

    Args:
        invoice_uuid: Invoice UUID
        item_uuid: Invoice item UUID
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Invoice item details

    Raises:
        HTTPException: If item not found
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.READ)

    try:
        item = await invoice_service.get_invoice_item_or_404(item_uuid)
        from .schemas import InvoiceItemResponse

        item_obj = InvoiceItemResponse.model_validate(item)
        return InvoiceItemDetailResponse(data=item_obj)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.put(
    "/invoices/{invoice_uuid}/items/{item_uuid}",
    response_model=InvoiceItemDetailResponse,
)
async def update_invoice_item(
    invoice_uuid: str,
    item_uuid: str,
    item_data: InvoiceItemUpdate,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Update an invoice item.

    Args:
        invoice_uuid: Invoice UUID
        item_uuid: Invoice item UUID
        item_data: Invoice item update data
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Updated invoice item

    Raises:
        HTTPException: If item not found or update fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.UPDATE)

    try:
        item = await invoice_service.update_invoice_item(
            item_uuid, item_data, user["user_id"]
        )
        from .schemas import InvoiceItemResponse

        item_obj = InvoiceItemResponse.model_validate(item)
        return InvoiceItemDetailResponse(data=item_obj)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update invoice item: {str(e)}",
        ) from e


@router.delete(
    "/invoices/{invoice_uuid}/items/{item_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_invoice_item(
    invoice_uuid: str,
    item_uuid: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Delete an invoice item.

    Args:
        invoice_uuid: Invoice UUID
        item_uuid: Invoice item UUID
        invoice_service: Invoice service instance
        user: Current user

    Raises:
        HTTPException: If item not found or deletion fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.UPDATE)

    try:
        await invoice_service.delete_invoice_item(item_uuid, user["user_id"])
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete invoice item: {str(e)}",
        ) from e


# Invoice Group Endpoints


@router.get("/invoice-groups", response_model=InvoiceGroupListResponse)
async def list_invoice_groups(
    status: Optional[str] = Query(None, description="Filter by status"),
    companyid: Optional[str] = Query(None, description="Filter by company UUID"),
    invoice_date_from: Optional[str] = Query(
        None, description="Filter by invoice date from (ISO format)"
    ),
    invoice_date_to: Optional[str] = Query(None, description="Filter by invoice date to (ISO format)"),
    due_date_from: Optional[str] = Query(None, description="Filter by due date from (ISO format)"),
    due_date_to: Optional[str] = Query(None, description="Filter by due date to (ISO format)"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query("invoice_date", description="Sort field"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """List invoice groups with filtering and pagination.

    Args:
        status: Filter by status
        companyid: Filter by company UUID
        invoice_date_from: Filter by invoice date from
        invoice_date_to: Filter by invoice date to
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
        Paginated list of invoice groups
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

    invoice_date_from_dt = parse_date(invoice_date_from)
    invoice_date_to_dt = parse_date(invoice_date_to)
    due_date_from_dt = parse_date(due_date_from)
    due_date_to_dt = parse_date(due_date_to)

    # Create filter params
    filters = InvoiceGroupFilterParams(
        status=status,
        companyid=companyid,
        invoice_date_from=invoice_date_from_dt,
        invoice_date_to=invoice_date_to_dt,
        due_date_from=due_date_from_dt,
        due_date_to=due_date_to_dt,
        currency=currency,
        page=page,
        page_size=page_size,
        sort_by=sort_by or "invoice_date",
        sort_order=sort_order or "desc",
    )

    # Validate pagination
    pagination = validate_pagination(page, page_size)

    # Get invoice groups
    groups, total = await invoice_service.list_invoice_groups(filters)

    # Convert dicts to InvoiceGroupResponse objects
    from .schemas import InvoiceGroupResponse

    group_objects = [InvoiceGroupResponse.model_validate(group) for group in groups]

    return InvoiceGroupListResponse(
        data=group_objects,
        pagination=paginate(pagination, total),
    )


@router.get("/invoice-groups/{group_uuid}", response_model=InvoiceGroupDetailResponse)
async def get_invoice_group(
    group_uuid: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Get an invoice group by UUID with invoices.

    Args:
        group_uuid: Invoice group UUID
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Invoice group details with invoices

    Raises:
        HTTPException: If invoice group not found
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.READ)

    try:
        group_dict = await invoice_service.get_invoice_group_with_invoices(group_uuid)
        from .schemas import InvoiceGroupResponse, InvoiceResponse

        group = InvoiceGroupResponse.model_validate(group_dict)
        invoices = [
            InvoiceResponse.model_validate(inv)
            for inv in group_dict.get("invoices", [])
        ]
        return InvoiceGroupDetailResponse(data=group, invoices=invoices)
    except InvoiceGroupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/invoice-groups",
    response_model=InvoiceGroupDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invoice_group(
    group_data: InvoiceGroupCreate,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Create a new invoice group.

    Args:
        group_data: Invoice group creation data
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Created invoice group

    Raises:
        HTTPException: If creation fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.CREATE)

    try:
        group_dict = await invoice_service.create_invoice_group(
            group_data, user["user_id"]
        )
        from .schemas import InvoiceGroupResponse

        group = InvoiceGroupResponse.model_validate(group_dict)
        return InvoiceGroupDetailResponse(data=group, invoices=[])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create invoice group: {str(e)}",
        ) from e


@router.put("/invoice-groups/{group_uuid}", response_model=InvoiceGroupDetailResponse)
async def update_invoice_group(
    group_uuid: str,
    group_data: InvoiceGroupUpdate,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Update an invoice group.

    Args:
        group_uuid: Invoice group UUID
        group_data: Invoice group update data
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Updated invoice group

    Raises:
        HTTPException: If invoice group not found or update fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.UPDATE)

    try:
        group_dict = await invoice_service.update_invoice_group(
            group_uuid, group_data, user["user_id"]
        )
        from .schemas import InvoiceGroupResponse

        group = InvoiceGroupResponse.model_validate(group_dict)
        return InvoiceGroupDetailResponse(data=group, invoices=[])
    except InvoiceGroupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update invoice group: {str(e)}",
        ) from e


@router.delete(
    "/invoice-groups/{group_uuid}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_invoice_group(
    group_uuid: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Delete an invoice group (soft delete).

    Args:
        group_uuid: Invoice group UUID
        invoice_service: Invoice service instance
        user: Current user

    Raises:
        HTTPException: If invoice group not found or deletion fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.DELETE)

    try:
        await invoice_service.delete_invoice_group(group_uuid, user["user_id"])
    except InvoiceGroupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete invoice group: {str(e)}",
        ) from e


@router.post(
    "/invoice-groups/{group_uuid}/add-invoice",
    response_model=InvoiceGroupDetailResponse,
)
async def add_invoice_to_group(
    group_uuid: str,
    request: AddInvoiceToGroupRequest,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Add an invoice to an invoice group.

    Args:
        group_uuid: Invoice group UUID
        request: Request with invoice UUID
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Updated invoice group with invoices

    Raises:
        HTTPException: If group or invoice not found
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.UPDATE)

    try:
        group_dict = await invoice_service.add_invoice_to_group(
            group_uuid, request.invoice_uuid, user["user_id"]
        )
        from .schemas import InvoiceGroupResponse, InvoiceResponse

        group = InvoiceGroupResponse.model_validate(group_dict)
        invoices = [
            InvoiceResponse.model_validate(inv)
            for inv in group_dict.get("invoices", [])
        ]
        return InvoiceGroupDetailResponse(data=group, invoices=invoices)
    except (InvoiceGroupNotFoundError, InvoiceNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add invoice to group: {str(e)}",
        ) from e


@router.post(
    "/invoice-groups/{group_uuid}/remove-invoice",
    response_model=InvoiceGroupDetailResponse,
)
async def remove_invoice_from_group(
    group_uuid: str,
    request: RemoveInvoiceFromGroupRequest,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Remove an invoice from an invoice group.

    Args:
        group_uuid: Invoice group UUID
        request: Request with invoice UUID
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Updated invoice group with invoices

    Raises:
        HTTPException: If group or invoice not found
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.UPDATE)

    try:
        group_dict = await invoice_service.remove_invoice_from_group(
            group_uuid, request.invoice_uuid, user["user_id"]
        )
        from .schemas import InvoiceGroupResponse, InvoiceResponse

        group = InvoiceGroupResponse.model_validate(group_dict)
        invoices = [
            InvoiceResponse.model_validate(inv)
            for inv in group_dict.get("invoices", [])
        ]
        return InvoiceGroupDetailResponse(data=group, invoices=invoices)
    except (InvoiceGroupNotFoundError, InvoiceNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to remove invoice from group: {str(e)}",
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
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to approve purchase order: {str(e)}",
        ) from e


# PO Milestone Endpoints


@router.get("/purchase-orders/{po_uuid}/milestones")
async def list_po_milestones(
    po_uuid: str,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """List all milestones for a purchase order.

    Args:
        po_uuid: Purchase order UUID
        po_service: Purchase order service instance
        user: Current user

    Returns:
        List of PO milestones

    Raises:
        HTTPException: If purchase order not found
    """
    # Check permission
    require_po_permission(user["role"], POPermission.READ)

    try:
        # Verify PO exists
        await po_service.get_purchase_order_or_404(po_uuid)

        milestones = await po_service.list_po_milestones(po_uuid)
        milestone_objects = [
            POMilestoneResponse.model_validate(m) for m in milestones
        ]
        return {"data": milestone_objects}
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/purchase-orders/{po_uuid}/milestones",
    response_model=POMilestoneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_po_milestone(
    po_uuid: str,
    milestone_data: POMilestoneCreate,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Create a new PO milestone.

    Args:
        po_uuid: Purchase order UUID
        milestone_data: Milestone creation data
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Created PO milestone

    Raises:
        HTTPException: If creation fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.UPDATE)

    try:
        milestone_dict = milestone_data.model_dump(exclude_unset=True)
        milestone = await po_service.create_po_milestone(
            po_uuid, milestone_dict, user["user_id"]
        )
        milestone_obj = POMilestoneResponse.model_validate(milestone)
        return milestone_obj
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create PO milestone: {str(e)}",
        ) from e


@router.put(
    "/purchase-orders/{po_uuid}/milestones/{milestone_uuid}",
    response_model=POMilestoneResponse,
)
async def update_po_milestone(
    po_uuid: str,
    milestone_uuid: str,
    milestone_data: POMilestoneUpdate,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Update a PO milestone.

    Args:
        po_uuid: Purchase order UUID
        milestone_uuid: PO milestone UUID
        milestone_data: Milestone update data
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Updated PO milestone

    Raises:
        HTTPException: If milestone not found or update fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.UPDATE)

    try:
        milestone_dict = milestone_data.model_dump(exclude_unset=True)
        milestone = await po_service.update_po_milestone(
            milestone_uuid, milestone_dict, user["user_id"]
        )
        milestone_obj = POMilestoneResponse.model_validate(milestone)
        return milestone_obj
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update PO milestone: {str(e)}",
        ) from e


# PO Disbursement Endpoints


@router.get(
    "/purchase-orders/{po_uuid}/disbursements",
    response_model=PODisbursementItemListResponse,
)
async def list_po_disbursements(
    po_uuid: str,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """List all disbursement items for a purchase order.

    Args:
        po_uuid: Purchase order UUID
        po_service: Purchase order service instance
        user: Current user

    Returns:
        List of PO disbursement items

    Raises:
        HTTPException: If purchase order not found
    """
    # Check permission
    require_po_permission(user["role"], POPermission.READ)

    try:
        # Verify PO exists
        await po_service.get_purchase_order_or_404(po_uuid)

        disbursements = await po_service.list_po_disbursements(po_uuid)
        disbursement_objects = [
            PODisbursementItemResponse.model_validate(d) for d in disbursements
        ]
        return PODisbursementItemListResponse(data=disbursement_objects)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/purchase-orders/{po_uuid}/disbursements",
    response_model=PODisbursementItemDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_po_disbursement(
    po_uuid: str,
    disbursement_data: PODisbursementItemCreate,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Create a new PO disbursement item.

    Args:
        po_uuid: Purchase order UUID
        disbursement_data: Disbursement creation data
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Created PO disbursement item

    Raises:
        HTTPException: If creation fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.UPDATE)

    try:
        disbursement_dict = disbursement_data.model_dump(exclude_unset=True)
        disbursement = await po_service.create_po_disbursement(
            po_uuid, disbursement_dict, user["user_id"]
        )
        disbursement_obj = PODisbursementItemResponse.model_validate(disbursement)
        return PODisbursementItemDetailResponse(data=disbursement_obj)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create PO disbursement: {str(e)}",
        ) from e


@router.put(
    "/purchase-orders/{po_uuid}/disbursements/{disbursement_uuid}",
    response_model=PODisbursementItemDetailResponse,
)
async def update_po_disbursement(
    po_uuid: str,
    disbursement_uuid: str,
    disbursement_data: PODisbursementItemUpdate,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Update a PO disbursement item.

    Args:
        po_uuid: Purchase order UUID
        disbursement_uuid: PO disbursement item UUID
        disbursement_data: Disbursement update data
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Updated PO disbursement item

    Raises:
        HTTPException: If disbursement not found or update fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.UPDATE)

    try:
        disbursement_dict = disbursement_data.model_dump(exclude_unset=True)
        disbursement = await po_service.update_po_disbursement(
            disbursement_uuid, disbursement_dict, user["user_id"]
        )
        disbursement_obj = PODisbursementItemResponse.model_validate(disbursement)
        return PODisbursementItemDetailResponse(data=disbursement_obj)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update PO disbursement: {str(e)}",
        ) from e


@router.delete(
    "/purchase-orders/{po_uuid}/disbursements/{disbursement_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_po_disbursement(
    po_uuid: str,
    disbursement_uuid: str,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Delete a PO disbursement item.

    Args:
        po_uuid: Purchase order UUID
        disbursement_uuid: PO disbursement item UUID
        po_service: Purchase order service instance
        user: Current user

    Raises:
        HTTPException: If disbursement not found or deletion fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.UPDATE)

    try:
        await po_service.delete_po_disbursement(disbursement_uuid, user["user_id"])
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete PO disbursement: {str(e)}",
        ) from e


# Archive/Restore Endpoints


@router.post("/invoices/{invoice_uuid}/archive", response_model=InvoiceDetailResponse)
async def archive_invoice(
    invoice_uuid: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Archive an invoice.

    Args:
        invoice_uuid: Invoice UUID
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Archived invoice

    Raises:
        HTTPException: If invoice not found or archiving fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.DELETE)

    try:
        invoice_dict = await invoice_service.archive_invoice(
            invoice_uuid, user["user_id"]
        )
        from .schemas import InvoiceResponse

        invoice = InvoiceResponse.model_validate(invoice_dict)
        return InvoiceDetailResponse(data=invoice)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to archive invoice: {str(e)}",
        ) from e


@router.post("/invoices/{invoice_uuid}/restore", response_model=InvoiceDetailResponse)
async def restore_invoice(
    invoice_uuid: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    user: dict = Depends(get_current_user_role),
):
    """Restore an archived invoice.

    Args:
        invoice_uuid: Invoice UUID
        invoice_service: Invoice service instance
        user: Current user

    Returns:
        Restored invoice

    Raises:
        HTTPException: If invoice not found or restoration fails
    """
    # Check permission
    require_invoice_permission(user["role"], InvoicePermission.UPDATE)

    try:
        invoice_dict = await invoice_service.restore_invoice(
            invoice_uuid, user["user_id"]
        )
        from .schemas import InvoiceResponse

        invoice = InvoiceResponse.model_validate(invoice_dict)
        return InvoiceDetailResponse(data=invoice)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to restore invoice: {str(e)}",
        ) from e


@router.post(
    "/purchase-orders/{po_uuid}/archive",
    response_model=PurchaseOrderDetailResponse,
)
async def archive_purchase_order(
    po_uuid: str,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Archive a purchase order.

    Args:
        po_uuid: Purchase order UUID
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Archived purchase order

    Raises:
        HTTPException: If purchase order not found or archiving fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.DELETE)

    try:
        po = await po_service.archive_purchase_order(po_uuid, user["user_id"])
        return PurchaseOrderDetailResponse(data=po)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to archive purchase order: {str(e)}",
        ) from e


@router.post(
    "/purchase-orders/{po_uuid}/restore",
    response_model=PurchaseOrderDetailResponse,
)
async def restore_purchase_order(
    po_uuid: str,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Restore an archived purchase order.

    Args:
        po_uuid: Purchase order UUID
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Restored purchase order

    Raises:
        HTTPException: If purchase order not found or restoration fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.UPDATE)

    try:
        po = await po_service.restore_purchase_order(po_uuid, user["user_id"])
        return PurchaseOrderDetailResponse(data=po)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to restore purchase order: {str(e)}",
        ) from e


# Batch Operations


@router.post(
    "/purchase-orders/batch-approve",
    response_model=BatchOperationResponse,
)
async def batch_approve_purchase_orders(
    request: BatchPOApproveRequest,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Approve multiple purchase orders.

    Args:
        request: Request with list of PO UUIDs
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Batch operation results

    Raises:
        HTTPException: If operation fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.APPROVE)

    try:
        result = await po_service.batch_approve_purchase_orders(
            request.po_uuids, user["user_id"]
        )
        return BatchOperationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to batch approve purchase orders: {str(e)}",
        ) from e


@router.post(
    "/purchase-orders/batch-delete",
    response_model=BatchOperationResponse,
)
async def batch_delete_purchase_orders(
    request: BatchPODeleteRequest,
    po_service: PurchaseOrderService = Depends(get_purchase_order_service),
    user: dict = Depends(get_current_user_role),
):
    """Delete multiple purchase orders (soft delete).

    Args:
        request: Request with list of PO UUIDs
        po_service: Purchase order service instance
        user: Current user

    Returns:
        Batch operation results

    Raises:
        HTTPException: If operation fails
    """
    # Check permission
    require_po_permission(user["role"], POPermission.DELETE)

    try:
        result = await po_service.batch_delete_purchase_orders(
            request.po_uuids, user["user_id"]
        )
        return BatchOperationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to batch delete purchase orders: {str(e)}",
        ) from e
