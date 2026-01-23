"""Sales Order service layer with business logic."""

from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Table, MetaData, Column, Integer, String

from ..invoices.models import Invoice
from .schemas import (
    SalesOrderCreate,
    SalesOrderFilterParams,
    SalesOrderUpdate,
    TransformToInvoiceRequest,
)


class SalesOrderNotFoundError(Exception):
    """Sales Order not found exception."""
    pass


class SalesOrderService:
    """Service for sales order operations.

    Note: Sales Orders are stored in the obj_tp_job_invoice table
    with invoice_type = 'Pro Forma' or 'Sales Order'
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Database session
        """
        self.db = db

    async def create_sales_order(
        self, so_data: SalesOrderCreate, user_id: str
    ) -> dict:
        """Create a new sales order.

        Args:
            so_data: Sales order creation data
            user_id: ID of user creating the SO

        Returns:
            Created sales order dict with job_uuid
        """
        so_dict = so_data.model_dump(exclude_unset=True)
        so_dict["created"] = datetime.now(timezone.utc)
        so_dict["modified"] = datetime.now(timezone.utc)
        so_dict["created_by"] = user_id
        so_dict["status"] = so_dict.get("status", "Draft")

        # Ensure invoice_type is set correctly
        if "invoice_type" not in so_dict or not so_dict["invoice_type"]:
            so_dict["invoice_type"] = "Pro Forma"

        invoice = Invoice(**so_dict)
        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)

        # Return enriched dict with job_uuid
        return await self.get_sales_order(invoice.obj_uuid)

    async def get_sales_order(self, so_uuid: str) -> Optional[dict]:
        """Get a sales order by UUID with enriched job data.

        Args:
            so_uuid: Sales order UUID

        Returns:
            Sales order dict with job_uuid if found, None otherwise
        """
        # Define Job table for joining
        metadata = MetaData()
        job_table = Table(
            "obj_tp_job",
            metadata,
            Column("obj_uuid", String(36), primary_key=True),
            Column("id", Integer),
            schema="franchise"
        )

        stmt = (
            select(
                Invoice,
                job_table.c.obj_uuid.label("job_uuid"),
            )
            .outerjoin(job_table, Invoice.jobid == job_table.c.id)
            .where(
                Invoice.obj_uuid == so_uuid,
                Invoice.deleted != True,
                Invoice.invoice_type.in_(["Pro Forma", "Sales Order"])
            )
        )
        result = await self.db.execute(stmt)
        row = result.first()

        if not row:
            return None

        # Convert to dict and add job_uuid
        invoice = row[0]
        invoice_dict = {c.name: getattr(invoice, c.name) for c in invoice.__table__.columns}
        invoice_dict["job_uuid"] = row[1]

        return invoice_dict

    async def get_sales_order_or_404(self, so_uuid: str) -> dict:
        """Get a sales order by UUID or raise 404.

        Args:
            so_uuid: Sales order UUID

        Returns:
            Sales order dict with job_uuid

        Raises:
            SalesOrderNotFoundError: If SO not found
        """
        so = await self.get_sales_order(so_uuid)
        if not so:
            raise SalesOrderNotFoundError(
                f"Sales order with UUID {so_uuid} not found"
            )
        return so

    async def update_sales_order(
        self, so_uuid: str, so_data: SalesOrderUpdate, user_id: str
    ) -> dict:
        """Update a sales order.

        Args:
            so_uuid: Sales order UUID
            so_data: Sales order update data
            user_id: ID of user updating the SO

        Returns:
            Updated sales order dict with job_uuid

        Raises:
            SalesOrderNotFoundError: If SO not found
        """
        # Get the actual Invoice model for updating
        stmt = select(Invoice).where(
            Invoice.obj_uuid == so_uuid,
            Invoice.deleted != True,
            Invoice.invoice_type.in_(["Pro Forma", "Sales Order"])
        )
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise SalesOrderNotFoundError(
                f"Sales order with UUID {so_uuid} not found"
            )

        update_data = so_data.model_dump(exclude_unset=True)
        update_data["modified"] = datetime.now(timezone.utc)
        update_data["modified_by"] = user_id

        for key, value in update_data.items():
            setattr(invoice, key, value)

        await self.db.commit()
        await self.db.refresh(invoice)

        # Return enriched dict with job_uuid
        return await self.get_sales_order(so_uuid)

    async def delete_sales_order(self, so_uuid: str, user_id: str) -> None:
        """Delete a sales order (soft delete).

        Args:
            so_uuid: Sales order UUID
            user_id: ID of user deleting the SO

        Raises:
            SalesOrderNotFoundError: If SO not found
        """
        stmt = select(Invoice).where(
            Invoice.obj_uuid == so_uuid,
            Invoice.deleted != True,
            Invoice.invoice_type.in_(["Pro Forma", "Sales Order"])
        )
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise SalesOrderNotFoundError(
                f"Sales order with UUID {so_uuid} not found"
            )

        invoice.deleted = True
        invoice.modified = datetime.now(timezone.utc)
        invoice.modified_by = user_id
        await self.db.commit()

    async def transform_to_invoice(
        self, so_uuid: str, transform_data: TransformToInvoiceRequest, user_id: str
    ) -> dict:
        """Transform a sales order to an invoice.

        Args:
            so_uuid: Sales order UUID
            transform_data: Transformation data
            user_id: ID of user performing transformation

        Returns:
            Transformed invoice dict with job_uuid

        Raises:
            SalesOrderNotFoundError: If SO not found
        """
        stmt = select(Invoice).where(
            Invoice.obj_uuid == so_uuid,
            Invoice.deleted != True,
            Invoice.invoice_type.in_(["Pro Forma", "Sales Order"])
        )
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise SalesOrderNotFoundError(
                f"Sales order with UUID {so_uuid} not found"
            )

        # Update invoice type and status
        invoice.invoice_type = transform_data.invoice_type or "Tax Invoice"
        invoice.status = "Draft"
        if transform_data.due_date:
            invoice.due_date = transform_data.due_date
        invoice.modified = datetime.now(timezone.utc)
        invoice.modified_by = user_id

        await self.db.commit()
        await self.db.refresh(invoice)

        # Return as invoice dict
        return await self.get_sales_order(so_uuid)

    async def cancel_sales_order(
        self, so_uuid: str, reason: Optional[str], user_id: str
    ) -> dict:
        """Cancel a sales order.

        Args:
            so_uuid: Sales order UUID
            reason: Cancellation reason
            user_id: ID of user cancelling the SO

        Returns:
            Cancelled sales order dict with job_uuid

        Raises:
            SalesOrderNotFoundError: If SO not found
        """
        stmt = select(Invoice).where(
            Invoice.obj_uuid == so_uuid,
            Invoice.deleted != True,
            Invoice.invoice_type.in_(["Pro Forma", "Sales Order"])
        )
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise SalesOrderNotFoundError(
                f"Sales order with UUID {so_uuid} not found"
            )

        invoice.status = "Cancelled"
        if reason:
            invoice.notes = (invoice.notes or "") + f"\n[Cancelled: {reason}]"
        invoice.modified = datetime.now(timezone.utc)
        invoice.modified_by = user_id

        await self.db.commit()
        await self.db.refresh(invoice)

        return await self.get_sales_order(so_uuid)

    async def list_sales_orders(
        self,
        filters: SalesOrderFilterParams,
    ) -> tuple[List[dict], int]:
        """List sales orders with filtering and pagination.

        Args:
            filters: Filter parameters

        Returns:
            Tuple of (sales orders list with job_uuid, total count)
        """
        # Define Job table for joining
        metadata = MetaData()
        job_table = Table(
            "obj_tp_job",
            metadata,
            Column("obj_uuid", String(36), primary_key=True),
            Column("id", Integer),
            schema="franchise"
        )

        stmt = (
            select(
                Invoice,
                job_table.c.obj_uuid.label("job_uuid"),
            )
            .outerjoin(job_table, Invoice.jobid == job_table.c.id)
            .where(
                Invoice.deleted != True,
                Invoice.invoice_type.in_(["Pro Forma", "Sales Order"])
            )
        )
        conditions = []

        # Apply filters
        if filters.status:
            conditions.append(Invoice.status == filters.status)

        if filters.job_id:
            conditions.append(Invoice.jobid == filters.job_id)

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
        count_stmt = select(func.count()).select_from(
            select(Invoice)
            .where(Invoice.deleted != True)
            .where(Invoice.invoice_type.in_(["Pro Forma", "Sales Order"]))
            .where(and_(*conditions) if conditions else True)
            .subquery()
        )
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
        rows = result.all()

        # Convert to dicts with job_uuid
        sales_orders = []
        for row in rows:
            invoice = row[0]
            invoice_dict = {c.name: getattr(invoice, c.name) for c in invoice.__table__.columns}
            invoice_dict["job_uuid"] = row[1]
            sales_orders.append(invoice_dict)

        return sales_orders, total
