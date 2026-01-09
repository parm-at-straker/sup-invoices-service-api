"""Invoice and Purchase Order service layer with business logic."""

from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Invoice, POMilestone, PurchaseOrder
from .schemas import (
    InvoiceCreate,
    InvoiceFilterParams,
    InvoiceUpdate,
    PurchaseOrderCreate,
    PurchaseOrderFilterParams,
    PurchaseOrderUpdate,
)


class InvoiceNotFoundError(Exception):
    """Invoice not found exception."""
    pass


class PurchaseOrderNotFoundError(Exception):
    """Purchase Order not found exception."""
    pass


class InvoiceService:
    """Service for invoice operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Database session
        """
        self.db = db

    async def create_invoice(self, invoice_data: InvoiceCreate, user_id: str) -> Invoice:
        """Create a new invoice.

        Args:
            invoice_data: Invoice creation data
            user_id: ID of user creating the invoice

        Returns:
            Created invoice
        """
        invoice_dict = invoice_data.model_dump(exclude_unset=True)
        invoice_dict["created"] = datetime.now(timezone.utc)
        invoice_dict["modified"] = datetime.now(timezone.utc)
        invoice_dict["created_by"] = user_id

        invoice = Invoice(**invoice_dict)
        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def get_invoice(self, invoice_uuid: str) -> Optional[Invoice]:
        """Get an invoice by UUID.

        Args:
            invoice_uuid: Invoice UUID

        Returns:
            Invoice if found, None otherwise
        """
        stmt = select(Invoice).where(
            Invoice.obj_uuid == invoice_uuid,
            Invoice.deleted != True
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_invoice_or_404(self, invoice_uuid: str) -> Invoice:
        """Get an invoice by UUID or raise 404.

        Args:
            invoice_uuid: Invoice UUID

        Returns:
            Invoice

        Raises:
            InvoiceNotFoundError: If invoice not found
        """
        invoice = await self.get_invoice(invoice_uuid)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice with UUID {invoice_uuid} not found")
        return invoice

    async def update_invoice(
        self, invoice_uuid: str, invoice_data: InvoiceUpdate, user_id: str
    ) -> Invoice:
        """Update an invoice.

        Args:
            invoice_uuid: Invoice UUID
            invoice_data: Invoice update data
            user_id: ID of user updating the invoice

        Returns:
            Updated invoice

        Raises:
            InvoiceNotFoundError: If invoice not found
        """
        invoice = await self.get_invoice_or_404(invoice_uuid)

        update_data = invoice_data.model_dump(exclude_unset=True)
        update_data["modified"] = datetime.now(timezone.utc)
        update_data["modified_by"] = user_id

        for key, value in update_data.items():
            setattr(invoice, key, value)

        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def delete_invoice(self, invoice_uuid: str, user_id: str) -> None:
        """Delete an invoice (soft delete).

        Args:
            invoice_uuid: Invoice UUID
            user_id: ID of user deleting the invoice

        Raises:
            InvoiceNotFoundError: If invoice not found
        """
        invoice = await self.get_invoice_or_404(invoice_uuid)
        invoice.deleted = True
        invoice.modified = datetime.now(timezone.utc)
        invoice.modified_by = user_id
        await self.db.commit()

    async def approve_invoice(self, invoice_uuid: str, user_id: str) -> Invoice:
        """Approve an invoice.

        Args:
            invoice_uuid: Invoice UUID
            user_id: ID of user approving the invoice

        Returns:
            Approved invoice

        Raises:
            InvoiceNotFoundError: If invoice not found
        """
        invoice = await self.get_invoice_or_404(invoice_uuid)
        invoice.status = "Approved"
        invoice.modified = datetime.now(timezone.utc)
        invoice.modified_by = user_id
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def list_invoices(
        self,
        filters: InvoiceFilterParams,
    ) -> tuple[List[Invoice], int]:
        """List invoices with filtering and pagination.

        Args:
            filters: Filter parameters

        Returns:
            Tuple of (invoices list, total count)
        """
        stmt = select(Invoice).where(Invoice.deleted != True)
        conditions = []

        # Apply filters
        if filters.status:
            conditions.append(Invoice.status == filters.status)

        if filters.job_id:
            conditions.append(Invoice.jobid == filters.job_id)

        if filters.invoice_group_id:
            conditions.append(Invoice.invoice_groupid == filters.invoice_group_id)

        if filters.client_name:
            conditions.append(Invoice.client_name.like(f"%{filters.client_name}%"))

        if filters.inv_date_from:
            conditions.append(Invoice.inv_date >= filters.inv_date_from)

        if filters.inv_date_to:
            conditions.append(Invoice.inv_date <= filters.inv_date_to)

        if filters.due_date_from:
            conditions.append(Invoice.due_date >= filters.due_date_from)

        if filters.due_date_to:
            conditions.append(Invoice.due_date <= filters.due_date_to)

        if filters.currency:
            conditions.append(Invoice.currency == filters.currency)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Get total count before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(Invoice, filters.sort_by, Invoice.inv_date)
        if filters.sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.offset(offset).limit(filters.page_size)

        result = await self.db.execute(stmt)
        invoices = result.scalars().all()
        return list(invoices), total


class PurchaseOrderService:
    """Service for purchase order operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Database session
        """
        self.db = db

    async def create_purchase_order(
        self, po_data: PurchaseOrderCreate, user_id: str
    ) -> PurchaseOrder:
        """Create a new purchase order.

        Args:
            po_data: Purchase order creation data
            user_id: ID of user creating the PO

        Returns:
            Created purchase order
        """
        po_dict = po_data.model_dump(exclude_unset=True)
        po_dict["created"] = datetime.now(timezone.utc)
        po_dict["modified"] = datetime.now(timezone.utc)

        po = PurchaseOrder(**po_dict)
        self.db.add(po)
        await self.db.commit()
        await self.db.refresh(po)
        return po

    async def get_purchase_order(self, po_uuid: str) -> Optional[PurchaseOrder]:
        """Get a purchase order by UUID.

        Args:
            po_uuid: Purchase order UUID

        Returns:
            Purchase order if found, None otherwise
        """
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.obj_uuid == po_uuid,
            PurchaseOrder.is_deleted != True
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_purchase_order_or_404(self, po_uuid: str) -> PurchaseOrder:
        """Get a purchase order by UUID or raise 404.

        Args:
            po_uuid: Purchase order UUID

        Returns:
            Purchase order

        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        po = await self.get_purchase_order(po_uuid)
        if not po:
            raise PurchaseOrderNotFoundError(
                f"Purchase order with UUID {po_uuid} not found"
            )
        return po

    async def update_purchase_order(
        self, po_uuid: str, po_data: PurchaseOrderUpdate, user_id: str
    ) -> PurchaseOrder:
        """Update a purchase order.

        Args:
            po_uuid: Purchase order UUID
            po_data: Purchase order update data
            user_id: ID of user updating the PO

        Returns:
            Updated purchase order

        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        po = await self.get_purchase_order_or_404(po_uuid)

        update_data = po_data.model_dump(exclude_unset=True)
        update_data["modified"] = datetime.now(timezone.utc)

        for key, value in update_data.items():
            setattr(po, key, value)

        await self.db.commit()
        await self.db.refresh(po)
        return po

    async def delete_purchase_order(self, po_uuid: str, user_id: str) -> None:
        """Delete a purchase order (soft delete).

        Args:
            po_uuid: Purchase order UUID
            user_id: ID of user deleting the PO

        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        po = await self.get_purchase_order_or_404(po_uuid)
        po.is_deleted = True
        po.modified = datetime.now(timezone.utc)
        await self.db.commit()

    async def approve_purchase_order(self, po_uuid: str, user_id: str) -> PurchaseOrder:
        """Approve a purchase order for payment.

        Args:
            po_uuid: Purchase order UUID
            user_id: ID of user approving the PO

        Returns:
            Approved purchase order

        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        po = await self.get_purchase_order_or_404(po_uuid)
        po.approvedforpayment = 1
        po.approveddate = datetime.now(timezone.utc)
        po.status = "Approved"
        po.modified = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(po)
        return po

    async def list_purchase_orders(
        self,
        filters: PurchaseOrderFilterParams,
    ) -> tuple[List[PurchaseOrder], int]:
        """List purchase orders with filtering and pagination.

        Args:
            filters: Filter parameters

        Returns:
            Tuple of (POs list, total count)
        """
        stmt = select(PurchaseOrder).where(PurchaseOrder.is_deleted != True)
        conditions = []

        # Apply filters
        if filters.status:
            conditions.append(PurchaseOrder.status == filters.status)

        if filters.job_id:
            conditions.append(PurchaseOrder.tp_job == filters.job_id)

        if filters.translator_id:
            conditions.append(PurchaseOrder.translatorid == filters.translator_id)

        if filters.project_manager_id:
            conditions.append(PurchaseOrder.projectmanagerid == filters.project_manager_id)

        if filters.order_date_from:
            conditions.append(PurchaseOrder.order_date >= filters.order_date_from)

        if filters.order_date_to:
            conditions.append(PurchaseOrder.order_date <= filters.order_date_to)

        if filters.date_due_from:
            conditions.append(PurchaseOrder.date_due >= filters.date_due_from)

        if filters.date_due_to:
            conditions.append(PurchaseOrder.date_due <= filters.date_due_to)

        if filters.currency:
            conditions.append(PurchaseOrder.currency == filters.currency)

        if filters.approved_for_payment is not None:
            if filters.approved_for_payment:
                conditions.append(PurchaseOrder.approvedforpayment == 1)
            else:
                conditions.append(
                    or_(
                        PurchaseOrder.approvedforpayment == 0,
                        PurchaseOrder.approvedforpayment.is_(None),
                    )
                )

        if filters.accepted is not None:
            conditions.append(PurchaseOrder.accepted == filters.accepted)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Get total count before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(PurchaseOrder, filters.sort_by, PurchaseOrder.order_date)
        if filters.sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.offset(offset).limit(filters.page_size)

        result = await self.db.execute(stmt)
        pos = result.scalars().all()
        return list(pos), total
