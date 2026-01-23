"""Sales Order Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from ..pagination import Pagination
from .enums import SalesOrderStatus


# Sales Order Schemas
# Note: Sales Orders are stored in the same obj_tp_job_invoice table
# with invoice_type = 'Pro Forma' or 'Sales Order'
class SalesOrderBase(BaseModel):
    """Base sales order schema with common fields."""

    jobid: Optional[int] = None
    amount_nett: Optional[float] = None
    currency: Optional[str] = None
    inv_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_address1: Optional[str] = None
    client_address2: Optional[str] = None
    client_city: Optional[str] = None
    client_postcode: Optional[str] = None
    client_region: Optional[str] = None
    client_country: Optional[str] = None
    notes: Optional[str] = None
    description: Optional[str] = None
    sl: Optional[str] = None
    tl: Optional[str] = None


class SalesOrderCreate(SalesOrderBase):
    """Schema for creating a new sales order."""

    jobid: int = Field(..., description="Job ID")
    amount_nett: float = Field(..., ge=0, description="Sales order net amount")
    currency: str = Field(..., description="Currency code")
    invoice_type: str = Field(
        default="Pro Forma", description="Invoice type (Pro Forma or Sales Order)"
    )


class SalesOrderUpdate(SalesOrderBase):
    """Schema for updating a sales order."""

    pass


class SalesOrderResponse(SalesOrderBase):
    """Schema for sales order response."""

    model_config = ConfigDict(from_attributes=True)

    obj_uuid: str
    id: Optional[int] = None
    inv_number: Optional[str] = None
    ns_inv_number: Optional[str] = None
    invoice_type: Optional[str] = None
    created_by: Optional[str] = None
    modified_by: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    job_uuid: Optional[str] = Field(None, description="Job UUID from joined obj_tp_job table")


class SalesOrderListResponse(BaseModel):
    """Schema for sales order list response."""

    data: list[SalesOrderResponse]
    pagination: Pagination


class SalesOrderDetailResponse(BaseModel):
    """Schema for single sales order detail response."""

    data: SalesOrderResponse


class SalesOrderFilterParams(BaseModel):
    """Query parameters for filtering sales orders."""

    model_config = ConfigDict(populate_by_name=True)

    status: Optional[str] = None
    job_id: Optional[int] = None
    group_id: Optional[str] = None
    inv_date_from: Optional[datetime] = None
    inv_date_to: Optional[datetime] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    currency: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    sort_by: Optional[str] = Field(default="inv_date")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")


class TransformToInvoiceRequest(BaseModel):
    """Schema for transforming sales order to invoice."""

    due_date: Optional[datetime] = None
    invoice_type: Optional[str] = Field(default="Tax Invoice", description="Target invoice type")


class CancelSalesOrderRequest(BaseModel):
    """Schema for cancelling a sales order."""

    reason: Optional[str] = None
