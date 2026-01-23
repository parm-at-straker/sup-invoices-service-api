"""Invoice and Purchase Order database models."""

import datetime
import uuid
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base


class Invoice(Base):
    """Invoice Model.

    Table: franchise.obj_tp_job_invoice
    Key: obj_uuid
    """

    __tablename__ = "obj_tp_job_invoice"
    __table_args__ = {"schema": "franchise"}

    # Primary Key
    obj_uuid: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Legacy ID
    id: Mapped[Optional[int]] = mapped_column(Integer, name="id")

    # Relationships
    jobid: Mapped[Optional[int]] = mapped_column(Integer, name="jobid")
    invoice_groupid: Mapped[Optional[int]] = mapped_column(
        Integer, name="invoice_groupid"
    )

    # Invoice Numbers
    inv_number: Mapped[Optional[str]] = mapped_column(String, name="inv_number")
    ns_inv_number: Mapped[Optional[str]] = mapped_column(String, name="ns_inv_number")
    xero_inv_number: Mapped[Optional[str]] = mapped_column(
        String, name="xero_inv_number"
    )
    DpsTxnRef: Mapped[Optional[str]] = mapped_column(String, name="DpsTxnRef")
    ref_inv: Mapped[Optional[str]] = mapped_column(String, name="ref_inv")

    # Dates
    inv_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="inv_date"
    )
    sent: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, name="sent")
    paid: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, name="paid")
    due_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="due_date"
    )

    # Financial
    currency: Mapped[Optional[str]] = mapped_column(String, name="currency")
    amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), name="amount")
    amount_nett: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), name="amount_nett"
    )
    job_total: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), name="job_total")
    job_total_nett: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), name="job_total_nett"
    )
    ex_rate_from_usd: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 4), name="ex_rate_from_usd"
    )
    ex_rate_to_nzd: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 4), name="ex_rate_to_nzd"
    )
    tax: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), name="tax")
    # Note: withholding_tax column doesn't exist in the database table
    # withholding_tax: Mapped[Optional[float]] = mapped_column(
    #     Numeric(10, 2), name="withholding_tax"
    # )
    tax_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), name="tax_rate")

    # Tax Flags
    zerorated: Mapped[Optional[bool]] = mapped_column(Boolean, name="zerorated")
    tax_exempt: Mapped[Optional[bool]] = mapped_column(Boolean, name="tax_exempt")
    tax_exempt_number: Mapped[Optional[str]] = mapped_column(
        String, name="tax_exempt_number"
    )
    tax_exempt_valid_to: Mapped[Optional[str]] = mapped_column(
        String, name="tax_exempt_valid_to"
    )

    # Type and Status
    transaction_type: Mapped[Optional[str]] = mapped_column(
        String, name="transaction_type"
    )
    invoice_type: Mapped[Optional[str]] = mapped_column(String, name="invoice_type")
    creditnote_type: Mapped[Optional[str]] = mapped_column(
        String, name="creditnote_type"
    )
    status: Mapped[Optional[str]] = mapped_column(String, name="status")

    # Languages
    sl: Mapped[Optional[str]] = mapped_column(String, name="sl")
    tl: Mapped[Optional[str]] = mapped_column(String, name="tl")

    # Client Information
    client_name: Mapped[Optional[str]] = mapped_column(String, name="client_name")
    client_email: Mapped[Optional[str]] = mapped_column(String, name="client_email")
    client_email_alt: Mapped[Optional[str]] = mapped_column(
        String, name="client_email_alt"
    )
    client_address1: Mapped[Optional[str]] = mapped_column(String, name="client_address1")
    client_address2: Mapped[Optional[str]] = mapped_column(String, name="client_address2")
    client_city: Mapped[Optional[str]] = mapped_column(String, name="client_city")
    client_postcode: Mapped[Optional[str]] = mapped_column(String, name="client_postcode")
    client_region: Mapped[Optional[str]] = mapped_column(String, name="client_region")
    client_country: Mapped[Optional[str]] = mapped_column(String, name="client_country")

    # Office Information
    office_address1: Mapped[Optional[str]] = mapped_column(
        String, name="office_address1"
    )
    office_address2: Mapped[Optional[str]] = mapped_column(
        String, name="office_address2"
    )
    office_city: Mapped[Optional[str]] = mapped_column(String, name="office_city")
    office_postcode: Mapped[Optional[str]] = mapped_column(
        String, name="office_postcode"
    )
    office_country: Mapped[Optional[str]] = mapped_column(String, name="office_country")
    office_region: Mapped[Optional[str]] = mapped_column(String, name="office_region")

    # Purchase Order
    purchase_order: Mapped[Optional[str]] = mapped_column(String, name="purchase_order")
    purchase_order_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="purchase_order_date"
    )

    # VAT Information
    vies_identifier: Mapped[Optional[str]] = mapped_column(String, name="vies_identifier")
    vat_country_code: Mapped[Optional[str]] = mapped_column(
        String, name="vat_country_code"
    )
    vat_number: Mapped[Optional[str]] = mapped_column(String, name="vat_number")
    vat_name: Mapped[Optional[str]] = mapped_column(String, name="vat_name")

    # Xero Integration
    xero_account: Mapped[Optional[str]] = mapped_column(String, name="xero_account")
    xerocode: Mapped[Optional[str]] = mapped_column(String, name="xerocode")

    # Other
    invoice_branding: Mapped[Optional[str]] = mapped_column(
        String, name="invoice_branding"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, name="notes")
    description: Mapped[Optional[str]] = mapped_column(Text, name="description")
    clients_identifier: Mapped[Optional[str]] = mapped_column(
        String, name="clients_identifier"
    )
    projectmanagerid: Mapped[Optional[str]] = mapped_column(
        String(36), name="projectmanagerid"
    )
    ns_customerid: Mapped[Optional[int]] = mapped_column(Integer, name="ns_customerid")

    # Flags
    deleted: Mapped[Optional[bool]] = mapped_column(Boolean, name="deleted")
    periodic_invoiced: Mapped[Optional[bool]] = mapped_column(
        Boolean, name="periodic_invoiced"
    )
    incl_source_files: Mapped[Optional[bool]] = mapped_column(
        Boolean, name="incl_source_files"
    )

    # Audit
    created_by: Mapped[Optional[str]] = mapped_column(String, name="created_by")
    modified_by: Mapped[Optional[str]] = mapped_column(String, name="modified_by")

    # Timestamps
    created: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="created"
    )
    modified: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="modified"
    )


class InvoiceGroup(Base):
    """Invoice Group Model.

    Table: franchise.obj_tp_job_invoice_group
    Key: obj_uuid
    """

    __tablename__ = "obj_tp_job_invoice_group"
    __table_args__ = {"schema": "franchise"}

    # Primary Key
    obj_uuid: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Legacy ID
    id: Mapped[Optional[int]] = mapped_column(Integer, name="id")

    # Dates
    invoice_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="invoice_date"
    )
    due_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="due_date"
    )
    sent: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, name="sent")
    paid: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, name="paid")

    # Relationships
    companyid: Mapped[Optional[str]] = mapped_column(String(36), name="companyid")
    entityid: Mapped[Optional[str]] = mapped_column(String(36), name="entityid")

    # Invoice Numbers
    xero_inv_number: Mapped[Optional[str]] = mapped_column(
        String, name="xero_inv_number"
    )

    # Financial
    currency: Mapped[Optional[str]] = mapped_column(String, name="currency")
    amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), name="amount")
    amount_nett: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), name="amount_nett"
    )
    tax: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), name="tax")
    # Note: withholding_tax column doesn't exist in the database table
    # withholding_tax: Mapped[Optional[float]] = mapped_column(
    #     Numeric(10, 2), name="withholding_tax"
    # )
    tax_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), name="tax_rate")

    # Tax Flags
    zerorated: Mapped[Optional[bool]] = mapped_column(Boolean, name="zerorated")
    tax_exempt: Mapped[Optional[bool]] = mapped_column(Boolean, name="tax_exempt")
    tax_exempt_number: Mapped[Optional[str]] = mapped_column(
        String, name="tax_exempt_number"
    )
    tax_exempt_valid_to: Mapped[Optional[str]] = mapped_column(
        String, name="tax_exempt_valid_to"
    )

    # Type and Status
    transaction_type: Mapped[Optional[str]] = mapped_column(
        String, name="transaction_type"
    )
    invoice_type: Mapped[Optional[str]] = mapped_column(String, name="invoice_type")
    status: Mapped[Optional[str]] = mapped_column(String, name="status")

    # Client Information
    client_name: Mapped[Optional[str]] = mapped_column(String, name="client_name")
    client_email: Mapped[Optional[str]] = mapped_column(String, name="client_email")
    client_address1: Mapped[Optional[str]] = mapped_column(String, name="client_address1")
    client_address2: Mapped[Optional[str]] = mapped_column(String, name="client_address2")
    client_city: Mapped[Optional[str]] = mapped_column(String, name="client_city")
    client_postcode: Mapped[Optional[str]] = mapped_column(String, name="client_postcode")
    client_country: Mapped[Optional[str]] = mapped_column(String, name="client_country")

    # Office Information
    office_address1: Mapped[Optional[str]] = mapped_column(
        String, name="office_address1"
    )
    office_address2: Mapped[Optional[str]] = mapped_column(
        String, name="office_address2"
    )
    office_city: Mapped[Optional[str]] = mapped_column(String, name="office_city")
    office_postcode: Mapped[Optional[str]] = mapped_column(
        String, name="office_postcode"
    )
    office_country: Mapped[Optional[str]] = mapped_column(String, name="office_country")
    office_region: Mapped[Optional[str]] = mapped_column(String, name="office_region")

    # VAT Information
    vies_identifier: Mapped[Optional[str]] = mapped_column(String, name="vies_identifier")
    vat_country_code: Mapped[Optional[str]] = mapped_column(
        String, name="vat_country_code"
    )
    vat_number: Mapped[Optional[str]] = mapped_column(String, name="vat_number")
    vat_name: Mapped[Optional[str]] = mapped_column(String, name="vat_name")

    # Xero Integration
    xero_account: Mapped[Optional[str]] = mapped_column(String, name="xero_account")

    # Other
    invoice_branding: Mapped[Optional[str]] = mapped_column(
        String, name="invoice_branding"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, name="notes")
    description: Mapped[Optional[str]] = mapped_column(Text, name="description")
    clients_identifier: Mapped[Optional[str]] = mapped_column(
        String, name="clients_identifier"
    )
    projectmanagerid: Mapped[Optional[str]] = mapped_column(
        String(36), name="projectmanagerid"
    )

    # Display Options
    incl_invoices: Mapped[Optional[bool]] = mapped_column(Boolean, name="incl_invoices")
    incl_job_title: Mapped[Optional[bool]] = mapped_column(Boolean, name="incl_job_title")
    incl_wordrate: Mapped[Optional[bool]] = mapped_column(Boolean, name="incl_wordrate")
    incl_wordcount: Mapped[Optional[bool]] = mapped_column(Boolean, name="incl_wordcount")
    incl_source_files: Mapped[Optional[bool]] = mapped_column(
        Boolean, name="incl_source_files"
    )
    incl_po: Mapped[Optional[bool]] = mapped_column(Boolean, name="incl_po")
    incl_po_date: Mapped[Optional[bool]] = mapped_column(Boolean, name="incl_po_date")
    incl_ref: Mapped[Optional[bool]] = mapped_column(Boolean, name="incl_ref")
    incl_leadtime: Mapped[Optional[bool]] = mapped_column(Boolean, name="incl_leadtime")
    inv_orderby_lang: Mapped[Optional[bool]] = mapped_column(
        Boolean, name="inv_orderby_lang"
    )

    # Flags
    deleted: Mapped[Optional[bool]] = mapped_column(Boolean, name="deleted")
    is_summary: Mapped[Optional[bool]] = mapped_column(Boolean, name="is_summary")

    # Audit
    created_by: Mapped[Optional[str]] = mapped_column(String, name="created_by")
    modified_by: Mapped[Optional[str]] = mapped_column(String, name="modified_by")

    # Timestamps
    created: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="created"
    )
    modified: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="modified"
    )


class InvoiceItem(Base):
    """Invoice Item Model.

    Table: franchise.obj_tp_job_invoice_item
    Key: obj_uuid
    """

    __tablename__ = "obj_tp_job_invoice_item"
    __table_args__ = {"schema": "franchise"}

    # Primary Key
    obj_uuid: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Legacy ID
    id: Mapped[Optional[int]] = mapped_column(Integer, name="id")

    # Relationships
    invoice_uuid: Mapped[Optional[str]] = mapped_column(
        String(36), name="invoice_uuid"
    )

    # Item Details
    item_type: Mapped[Optional[str]] = mapped_column(String, name="item_type")
    source_lang: Mapped[Optional[str]] = mapped_column(String, name="source_lang")
    target_lang: Mapped[Optional[str]] = mapped_column(String, name="target_lang")
    currency: Mapped[Optional[str]] = mapped_column(String, name="currency")
    unit_price: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), name="unit_price"
    )
    amount_nett: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), name="amount_nett"
    )

    # Timestamps
    created: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="created"
    )
    modified: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="modified"
    )


class PurchaseOrder(Base):
    """Purchase Order Model.

    Table: franchise.obj_tp_purchaseorder
    Key: obj_uuid
    """

    __tablename__ = "obj_tp_purchaseorder"
    __table_args__ = {"schema": "franchise"}

    # Primary Key
    obj_uuid: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Relationships
    tp_invoice: Mapped[Optional[str]] = mapped_column(String(36), name="tp_invoice")
    translatorid: Mapped[Optional[str]] = mapped_column(String(36), name="translatorid")
    projectmanagerid: Mapped[Optional[str]] = mapped_column(
        String(36), name="projectmanagerid"
    )
    tp_job: Mapped[Optional[str]] = mapped_column(String(36), name="tp_job")
    bid_uuid: Mapped[Optional[str]] = mapped_column(String(36), name="bid_uuid")
    agency_translatorid: Mapped[Optional[str]] = mapped_column(
        String(36), name="agency_translatorid"
    )
    agency_editorid: Mapped[Optional[str]] = mapped_column(
        String(36), name="agency_editorid"
    )
    job_pass_uuid: Mapped[Optional[str]] = mapped_column(
        String(36), name="job_pass_uuid"
    )

    # Order Details
    orderno: Mapped[Optional[int]] = mapped_column(Integer, name="orderno")
    order_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="order_date"
    )
    order_notes: Mapped[Optional[str]] = mapped_column(Text, name="order_notes")

    # Financial
    paymentid: Mapped[Optional[str]] = mapped_column(String(36), name="paymentid")
    amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), name="amount")
    amount_nett: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), name="amount_nett"
    )
    currency: Mapped[Optional[str]] = mapped_column(String, name="currency")
    ex_rate_to_usd: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 4), name="ex_rate_to_usd"
    )
    translator_amt: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), name="translator_amt"
    )

    # Time Tracking
    time_mins: Mapped[Optional[int]] = mapped_column(Integer, name="time_mins")

    # Status
    status: Mapped[Optional[str]] = mapped_column(String, name="status")
    approvedforpayment: Mapped[Optional[int]] = mapped_column(
        Integer, name="approvedforpayment"
    )
    accepted: Mapped[Optional[bool]] = mapped_column(Boolean, name="accepted")
    dateaccepted: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="dateaccepted"
    )

    # Languages
    target_lang: Mapped[Optional[str]] = mapped_column(String, name="target_lang")

    # Dates
    date_start: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="date_start"
    )
    date_due: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="date_due"
    )

    # Milestones
    milestone25complete: Mapped[Optional[int]] = mapped_column(
        Integer, name="milestone25complete"
    )
    milestone50complete: Mapped[Optional[int]] = mapped_column(
        Integer, name="milestone50complete"
    )
    milestone75complete: Mapped[Optional[int]] = mapped_column(
        Integer, name="milestone75complete"
    )

    # Payment
    translator_paid: Mapped[Optional[bool]] = mapped_column(
        Boolean, name="translator_paid"
    )
    paymentreference: Mapped[Optional[str]] = mapped_column(
        String, name="paymentreference"
    )
    paymentdate: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="paymentdate"
    )
    paymentnotes: Mapped[Optional[str]] = mapped_column(Text, name="paymentnotes")

    # Xero Integration
    loaded_xero: Mapped[Optional[bool]] = mapped_column(Boolean, name="loaded_xero")
    approved_xero: Mapped[Optional[bool]] = mapped_column(Boolean, name="approved_xero")
    rechargedate: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="rechargedate"
    )

    # Approval
    approveddate: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="approveddate"
    )

    # Other
    translator_note: Mapped[Optional[str]] = mapped_column(Text, name="translator_note")
    nonnative_translator: Mapped[Optional[str]] = mapped_column(
        Text, name="nonnative_translator"
    )
    po_type: Mapped[Optional[str]] = mapped_column(String, name="po_type")
    po_subtype: Mapped[Optional[str]] = mapped_column(String, name="po_subtype")
    decline_note: Mapped[Optional[str]] = mapped_column(Text, name="decline_note")
    revoke_note: Mapped[Optional[str]] = mapped_column(Text, name="revoke_note")
    po_file_analysis_file: Mapped[Optional[str]] = mapped_column(
        String, name="po_file_analysis_file"
    )

    # Flags
    disputed_po: Mapped[Optional[bool]] = mapped_column(Boolean, name="disputed_po")
    expired_po: Mapped[Optional[bool]] = mapped_column(Boolean, name="expired_po")
    expired_email_sent: Mapped[Optional[bool]] = mapped_column(
        Boolean, name="expired_email_sent"
    )
    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean, name="is_deleted")
    is_declined: Mapped[Optional[bool]] = mapped_column(Boolean, name="is_declined")
    is_prebooked: Mapped[Optional[bool]] = mapped_column(Boolean, name="is_prebooked")
    is_internal: Mapped[Optional[int]] = mapped_column(Integer, name="is_internal")

    # QA
    qa_checked_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="qa_checked_date"
    )

    # Timestamps
    created: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="created"
    )
    modified: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="modified"
    )


class POMilestone(Base):
    """Purchase Order Milestone Model.

    Table: franchise.obj_tp_po_milestones
    Key: obj_uuid
    """

    __tablename__ = "obj_tp_po_milestones"
    __table_args__ = {"schema": "franchise"}

    # Primary Key
    obj_uuid: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Relationships
    tp_purchaseorder: Mapped[Optional[str]] = mapped_column(
        String(36), name="tp_purchaseorder"
    )

    # Milestone Details
    milestone: Mapped[Optional[int]] = mapped_column(Integer, name="milestone")
    date_completed: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="date_completed"
    )
    confirmed: Mapped[Optional[int]] = mapped_column(Integer, name="confirmed")
    notes: Mapped[Optional[str]] = mapped_column(Text, name="notes")
    remote_ip: Mapped[Optional[str]] = mapped_column(String, name="remote_ip")

    # Timestamps
    created: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="created"
    )
    modified: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="modified"
    )


class PODisbursementItem(Base):
    """Purchase Order Disbursement Item Model.

    Table: franchise.obj_tp_po_disbursements_item
    Key: obj_uuid
    """

    __tablename__ = "obj_tp_po_disbursements_item"
    __table_args__ = {"schema": "franchise"}

    # Primary Key
    obj_uuid: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Relationships
    po_uuid: Mapped[Optional[str]] = mapped_column(String(36), name="po_uuid")

    # Item Details
    item_type: Mapped[Optional[str]] = mapped_column(String, name="item_type")
    item_type_info: Mapped[Optional[str]] = mapped_column(Text, name="item_type_info")
    no_of_units: Mapped[Optional[int]] = mapped_column(Integer, name="no_of_units")
    rate_per_unit: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), name="rate_per_unit"
    )
    total_cost: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), name="total_cost"
    )

    # Timestamps
    created: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="created"
    )
    modified: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, name="modified"
    )

