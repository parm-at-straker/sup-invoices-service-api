"""Invoice and Purchase Order Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..pagination import Pagination
from .enums import InvoiceStatus, POStatus


# Invoice Schemas
class InvoiceBase(BaseModel):
    """Base invoice schema with common fields."""

    jobid: Optional[int] = None
    invoice_groupid: Optional[int] = None
    inv_number: Optional[str] = None
    ns_inv_number: Optional[str] = None
    xero_inv_number: Optional[str] = None
    DpsTxnRef: Optional[str] = None
    ref_inv: Optional[str] = None
    inv_date: Optional[datetime] = None
    sent: Optional[datetime] = None
    paid: Optional[datetime] = None
    due_date: Optional[datetime] = None
    currency: Optional[str] = None
    amount: Optional[float] = None
    amount_nett: Optional[float] = None
    job_total: Optional[float] = None
    job_total_nett: Optional[float] = None
    ex_rate_from_usd: Optional[float] = None
    ex_rate_to_nzd: Optional[float] = None
    tax: Optional[float] = None
    # Note: withholding_tax column doesn't exist in the database table
    # withholding_tax: Optional[float] = None
    tax_rate: Optional[float] = None
    zerorated: Optional[bool] = None
    tax_exempt: Optional[bool] = None
    tax_exempt_number: Optional[str] = None
    tax_exempt_valid_to: Optional[str] = None
    transaction_type: Optional[str] = None
    invoice_type: Optional[str] = None
    creditnote_type: Optional[str] = None
    status: Optional[str] = None
    sl: Optional[str] = None
    tl: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_email_alt: Optional[str] = None
    client_address1: Optional[str] = None
    client_address2: Optional[str] = None
    client_city: Optional[str] = None
    client_postcode: Optional[str] = None
    client_region: Optional[str] = None
    client_country: Optional[str] = None
    office_address1: Optional[str] = None
    office_address2: Optional[str] = None
    office_city: Optional[str] = None
    office_postcode: Optional[str] = None
    office_country: Optional[str] = None
    office_region: Optional[str] = None
    purchase_order: Optional[str] = None
    purchase_order_date: Optional[datetime] = None
    vies_identifier: Optional[str] = None
    vat_country_code: Optional[str] = None
    vat_number: Optional[str] = None
    vat_name: Optional[str] = None
    xero_account: Optional[str] = None
    xerocode: Optional[str] = None
    invoice_branding: Optional[str] = None
    notes: Optional[str] = None
    description: Optional[str] = None
    clients_identifier: Optional[str] = None
    projectmanagerid: Optional[str] = Field(None, max_length=36)
    ns_customerid: Optional[int] = None
    deleted: Optional[bool] = None
    periodic_invoiced: Optional[bool] = None
    incl_source_files: Optional[bool] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating a new invoice."""

    jobid: int = Field(..., description="Job ID")
    currency: str = Field(..., description="Currency code")
    amount: float = Field(..., ge=0, description="Invoice amount")
    status: Optional[str] = Field(default="Draft", description="Invoice status")


class InvoiceUpdate(InvoiceBase):
    """Schema for updating an invoice."""

    pass


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    model_config = ConfigDict(from_attributes=True)

    obj_uuid: str
    id: Optional[int] = None
    created_by: Optional[str] = None
    modified_by: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

    # Enriched fields (from joins)
    job_uuid: Optional[str] = Field(None, description="Job UUID from joined obj_tp_job table")


class InvoiceListResponse(BaseModel):
    """Schema for invoice list response."""

    data: list[InvoiceResponse]
    pagination: Pagination


class InvoiceDetailResponse(BaseModel):
    """Schema for single invoice detail response."""

    data: InvoiceResponse


class InvoiceFilterParams(BaseModel):
    """Query parameters for filtering invoices."""

    model_config = ConfigDict(populate_by_name=True)

    status: Optional[str] = None
    job_id: Optional[int] = Field(None, alias="job_id")
    invoice_group_id: Optional[int] = Field(None, alias="invoice_group_id")
    client_name: Optional[str] = Field(None, alias="client_name")
    inv_date_from: Optional[datetime] = None
    inv_date_to: Optional[datetime] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    currency: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    sort_by: Optional[str] = Field(default="inv_date")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")


# Purchase Order Schemas
class PurchaseOrderBase(BaseModel):
    """Base purchase order schema with common fields."""

    tp_invoice: Optional[str] = Field(None, max_length=36)
    translatorid: Optional[str] = Field(None, max_length=36)
    projectmanagerid: Optional[str] = Field(None, max_length=36)
    tp_job: Optional[str] = Field(None, max_length=36)
    bid_uuid: Optional[str] = Field(None, max_length=36)
    agency_translatorid: Optional[str] = Field(None, max_length=36)
    agency_editorid: Optional[str] = Field(None, max_length=36)
    job_pass_uuid: Optional[str] = Field(None, max_length=36)
    orderno: Optional[int] = None
    order_date: Optional[datetime] = None
    order_notes: Optional[str] = None
    paymentid: Optional[str] = Field(None, max_length=36)
    amount: Optional[float] = None
    amount_nett: Optional[float] = None
    currency: Optional[str] = None
    ex_rate_to_usd: Optional[float] = None
    translator_amt: Optional[float] = None
    time_mins: Optional[int] = None
    status: Optional[str] = None
    approvedforpayment: Optional[int] = None
    accepted: Optional[bool] = None
    dateaccepted: Optional[datetime] = None
    target_lang: Optional[str] = None
    date_start: Optional[datetime] = None
    date_due: Optional[datetime] = None
    milestone25complete: Optional[int] = None
    milestone50complete: Optional[int] = None
    milestone75complete: Optional[int] = None
    translator_paid: Optional[bool] = None
    paymentreference: Optional[str] = None
    paymentdate: Optional[datetime] = None
    paymentnotes: Optional[str] = None
    loaded_xero: Optional[bool] = None
    approved_xero: Optional[bool] = None
    rechargedate: Optional[datetime] = None
    approveddate: Optional[datetime] = None
    translator_note: Optional[str] = None
    nonnative_translator: Optional[str] = None
    po_type: Optional[str] = None
    po_subtype: Optional[str] = None
    decline_note: Optional[str] = None
    revoke_note: Optional[str] = None
    po_file_analysis_file: Optional[str] = None
    disputed_po: Optional[bool] = None
    expired_po: Optional[bool] = None
    expired_email_sent: Optional[bool] = None
    is_deleted: Optional[bool] = None
    is_declined: Optional[bool] = None
    is_prebooked: Optional[bool] = None
    is_internal: Optional[int] = None
    qa_checked_date: Optional[datetime] = None

    @field_validator("is_internal", mode="before")
    @classmethod
    def convert_bytes_to_int(cls, v):
        """Convert bytes from MySQL boolean to int."""
        if isinstance(v, bytes):
            return int.from_bytes(v, byteorder="big")
        return v


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a new purchase order."""

    translatorid: str = Field(..., max_length=36, description="Translator UUID")
    tp_job: str = Field(..., max_length=36, description="Job UUID")
    amount: float = Field(..., ge=0, description="PO amount")
    currency: str = Field(..., description="Currency code")
    status: Optional[str] = Field(default="Pending", description="PO status")


class PurchaseOrderUpdate(PurchaseOrderBase):
    """Schema for updating a purchase order."""

    pass


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""

    model_config = ConfigDict(from_attributes=True)

    obj_uuid: str
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

    # Enriched fields (from joins)
    job_id: Optional[int] = Field(None, description="Job ID from joined obj_tp_job table")


class PurchaseOrderListResponse(BaseModel):
    """Schema for purchase order list response."""

    data: list[PurchaseOrderResponse]
    pagination: Pagination


class PurchaseOrderDetailResponse(BaseModel):
    """Schema for single purchase order detail response."""

    data: PurchaseOrderResponse


class PurchaseOrderFilterParams(BaseModel):
    """Query parameters for filtering purchase orders."""

    model_config = ConfigDict(populate_by_name=True)

    status: Optional[str] = None
    job_id: Optional[str] = Field(None, alias="job_id")
    translator_id: Optional[str] = Field(None, alias="translator_id")
    project_manager_id: Optional[str] = Field(None, alias="project_manager_id")
    order_date_from: Optional[datetime] = None
    order_date_to: Optional[datetime] = None
    date_due_from: Optional[datetime] = None
    date_due_to: Optional[datetime] = None
    currency: Optional[str] = None
    approved_for_payment: Optional[bool] = None
    accepted: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    sort_by: Optional[str] = Field(default="order_date")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")


# POMilestone Schemas
class POMilestoneBase(BaseModel):
    """Base PO milestone schema."""

    tp_purchaseorder: Optional[str] = Field(None, max_length=36)
    milestone: Optional[int] = None
    date_completed: Optional[datetime] = None
    confirmed: Optional[int] = None
    notes: Optional[str] = None
    remote_ip: Optional[str] = None


class POMilestoneCreate(POMilestoneBase):
    """Schema for creating a PO milestone."""

    tp_purchaseorder: str = Field(..., max_length=36, description="Purchase Order UUID")
    milestone: int = Field(..., ge=1, le=100, description="Milestone percentage")


class POMilestoneResponse(POMilestoneBase):
    """Schema for PO milestone response."""

    model_config = ConfigDict(from_attributes=True)

    obj_uuid: str
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
