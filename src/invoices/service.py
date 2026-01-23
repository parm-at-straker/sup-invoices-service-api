"""Invoice and Purchase Order service layer with business logic."""

from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Invoice,
    InvoiceGroup,
    InvoiceItem,
    POMilestone,
    PODisbursementItem,
    PurchaseOrder,
)
from .schemas import (
    InvoiceCreate,
    InvoiceFilterParams,
    InvoiceUpdate,
    InvoiceItemCreate,
    InvoiceItemUpdate,
    InvoiceGroupCreate,
    InvoiceGroupFilterParams,
    InvoiceGroupUpdate,
    PurchaseOrderCreate,
    PurchaseOrderFilterParams,
    PurchaseOrderUpdate,
)
from .workflow import (
    InvalidStatusTransitionError,
    validate_invoice_status_transition,
    validate_po_status_transition,
)


class InvoiceNotFoundError(Exception):
    """Invoice not found exception."""
    pass


class InvoiceGroupNotFoundError(Exception):
    """Invoice Group not found exception."""
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

    async def create_invoice(self, invoice_data: InvoiceCreate, user_id: str) -> dict:
        """Create a new invoice.

        Args:
            invoice_data: Invoice creation data
            user_id: ID of user creating the invoice

        Returns:
            Created invoice dict with job_uuid
        """
        invoice_dict = invoice_data.model_dump(exclude_unset=True)
        invoice_dict["created"] = datetime.now(timezone.utc)
        invoice_dict["modified"] = datetime.now(timezone.utc)
        invoice_dict["created_by"] = user_id

        invoice = Invoice(**invoice_dict)
        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)

        return await self.get_invoice(invoice.obj_uuid)

    async def get_invoice(self, invoice_uuid: str) -> Optional[dict]:
        """Get an invoice by UUID with enriched job data.

        Args:
            invoice_uuid: Invoice UUID

        Returns:
            Invoice dict with job_uuid if found, None otherwise
        """
        from sqlalchemy import Table, MetaData, Column, Integer, String

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
                Invoice.obj_uuid == invoice_uuid,
                Invoice.deleted != True
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

    async def get_invoice_or_404(self, invoice_uuid: str) -> dict:
        """Get an invoice by UUID or raise 404.

        Args:
            invoice_uuid: Invoice UUID

        Returns:
            Invoice dict

        Raises:
            InvoiceNotFoundError: If invoice not found
        """
        invoice = await self.get_invoice(invoice_uuid)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice with UUID {invoice_uuid} not found")
        return invoice

    async def update_invoice(
        self, invoice_uuid: str, invoice_data: InvoiceUpdate, user_id: str
    ) -> dict:
        """Update an invoice.

        Args:
            invoice_uuid: Invoice UUID
            invoice_data: Invoice update data
            user_id: ID of user updating the invoice

        Returns:
            Updated invoice dict

        Raises:
            InvoiceNotFoundError: If invoice not found
        """
        await self.get_invoice_or_404(invoice_uuid)  # Verify exists

        stmt = select(Invoice).where(
            Invoice.obj_uuid == invoice_uuid,
            Invoice.deleted != True
        )
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise InvoiceNotFoundError(f"Invoice with UUID {invoice_uuid} not found")

        update_data = invoice_data.model_dump(exclude_unset=True)
        update_data["modified"] = datetime.now(timezone.utc)
        update_data["modified_by"] = user_id

        # Validate status transition if status is being updated
        if "status" in update_data and invoice.status:
            validate_invoice_status_transition(invoice.status, update_data["status"])

        for key, value in update_data.items():
            setattr(invoice, key, value)

        await self.db.commit()
        await self.db.refresh(invoice)

        return await self.get_invoice(invoice_uuid)

    async def delete_invoice(self, invoice_uuid: str, user_id: str) -> None:
        """Delete an invoice (soft delete).

        Args:
            invoice_uuid: Invoice UUID
            user_id: ID of user deleting the invoice

        Raises:
            InvoiceNotFoundError: If invoice not found
        """
        await self.get_invoice_or_404(invoice_uuid)  # Verify exists

        stmt = select(Invoice).where(
            Invoice.obj_uuid == invoice_uuid,
            Invoice.deleted != True
        )
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise InvoiceNotFoundError(f"Invoice with UUID {invoice_uuid} not found")

        invoice.deleted = True
        invoice.modified = datetime.now(timezone.utc)
        invoice.modified_by = user_id
        await self.db.commit()

    async def archive_invoice(self, invoice_uuid: str, user_id: str) -> dict:
        """Archive an invoice.

        Args:
            invoice_uuid: Invoice UUID
            user_id: ID of user archiving the invoice

        Returns:
            Archived invoice dict

        Raises:
            InvoiceNotFoundError: If invoice not found
        """
        await self.get_invoice_or_404(invoice_uuid)  # Verify exists

        stmt = select(Invoice).where(
            Invoice.obj_uuid == invoice_uuid,
            Invoice.deleted != True
        )
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise InvoiceNotFoundError(f"Invoice with UUID {invoice_uuid} not found")

        invoice.deleted = True  # Use deleted flag for archiving
        invoice.status = "Archived"
        invoice.modified = datetime.now(timezone.utc)
        invoice.modified_by = user_id
        await self.db.commit()

        return await self.get_invoice(invoice_uuid)

    async def restore_invoice(self, invoice_uuid: str, user_id: str) -> dict:
        """Restore an archived invoice.

        Args:
            invoice_uuid: Invoice UUID
            user_id: ID of user restoring the invoice

        Returns:
            Restored invoice dict

        Raises:
            InvoiceNotFoundError: If invoice not found
        """
        # Get invoice even if deleted (archived)
        stmt = select(Invoice).where(Invoice.obj_uuid == invoice_uuid)
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise InvoiceNotFoundError(f"Invoice with UUID {invoice_uuid} not found")

        invoice.deleted = False
        if invoice.status == "Archived":
            invoice.status = "Draft"  # Restore to draft status
        invoice.modified = datetime.now(timezone.utc)
        invoice.modified_by = user_id
        await self.db.commit()

        return await self.get_invoice(invoice_uuid)

    async def approve_invoice(self, invoice_uuid: str, user_id: str) -> dict:
        """Approve an invoice.

        Args:
            invoice_uuid: Invoice UUID
            user_id: ID of user approving the invoice

        Returns:
            Approved invoice dict

        Raises:
            InvoiceNotFoundError: If invoice not found
        """
        await self.get_invoice_or_404(invoice_uuid)  # Verify exists

        stmt = select(Invoice).where(
            Invoice.obj_uuid == invoice_uuid,
            Invoice.deleted != True
        )
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise InvoiceNotFoundError(f"Invoice with UUID {invoice_uuid} not found")

        # Validate status transition
        validate_invoice_status_transition(invoice.status or "Draft", "Approved")

        invoice.status = "Approved"
        invoice.modified = datetime.now(timezone.utc)
        invoice.modified_by = user_id
        await self.db.commit()
        await self.db.refresh(invoice)

        return await self.get_invoice(invoice_uuid)

    async def list_invoices(
        self,
        filters: InvoiceFilterParams,
    ) -> tuple[List[dict], int]:
        """List invoices with filtering and pagination.

        Args:
            filters: Filter parameters

        Returns:
            Tuple of (invoices list with job_uuid, total count)
        """
        from sqlalchemy import Table, MetaData, Column, Integer, String

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
            .where(Invoice.deleted != True)
        )
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
        count_stmt = select(func.count()).select_from(
            select(Invoice)
            .where(Invoice.deleted != True)
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
        invoices = []
        for row in rows:
            invoice = row[0]
            invoice_dict = {c.name: getattr(invoice, c.name) for c in invoice.__table__.columns}
            invoice_dict["job_uuid"] = row[1]
            invoices.append(invoice_dict)

        return invoices, total

    async def list_invoice_items(self, invoice_uuid: str) -> List[dict]:
        """List all items for an invoice.

        Args:
            invoice_uuid: Invoice UUID

        Returns:
            List of invoice item dicts
        """
        stmt = (
            select(InvoiceItem)
            .where(InvoiceItem.invoice_uuid == invoice_uuid)
            .order_by(InvoiceItem.item_type, InvoiceItem.target_lang)
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return [
            {c.name: getattr(item, c.name) for c in item.__table__.columns}
            for item in items
        ]

    async def create_invoice_item(
        self, invoice_uuid: str, item_data: InvoiceItemCreate, user_id: str
    ) -> dict:
        """Create a new invoice item.

        Args:
            invoice_uuid: Invoice UUID
            item_data: Invoice item creation data
            user_id: ID of user creating the item

        Returns:
            Created invoice item dict
        """
        # Verify invoice exists
        await self.get_invoice_or_404(invoice_uuid)

        item_dict = item_data.model_dump(exclude_unset=True)
        item_dict["invoice_uuid"] = invoice_uuid
        item_dict["created"] = datetime.now(timezone.utc)
        item_dict["modified"] = datetime.now(timezone.utc)

        item = InvoiceItem(**item_dict)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        return {c.name: getattr(item, c.name) for c in item.__table__.columns}

    async def get_invoice_item(self, item_uuid: str) -> Optional[dict]:
        """Get an invoice item by UUID.

        Args:
            item_uuid: Invoice item UUID

        Returns:
            Invoice item dict if found, None otherwise
        """
        stmt = select(InvoiceItem).where(InvoiceItem.obj_uuid == item_uuid)
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            return None

        return {c.name: getattr(item, c.name) for c in item.__table__.columns}

    async def get_invoice_item_or_404(self, item_uuid: str) -> dict:
        """Get an invoice item by UUID or raise 404.

        Args:
            item_uuid: Invoice item UUID

        Returns:
            Invoice item dict

        Raises:
            InvoiceNotFoundError: If item not found
        """
        item = await self.get_invoice_item(item_uuid)
        if not item:
            raise InvoiceNotFoundError(
                f"Invoice item with UUID {item_uuid} not found"
            )
        return item

    async def update_invoice_item(
        self, item_uuid: str, item_data: InvoiceItemUpdate, user_id: str
    ) -> dict:
        """Update an invoice item.

        Args:
            item_uuid: Invoice item UUID
            item_data: Invoice item update data
            user_id: ID of user updating the item

        Returns:
            Updated invoice item dict

        Raises:
            InvoiceNotFoundError: If item not found
        """
        stmt = select(InvoiceItem).where(InvoiceItem.obj_uuid == item_uuid)
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise InvoiceNotFoundError(
                f"Invoice item with UUID {item_uuid} not found"
            )

        update_data = item_data.model_dump(exclude_unset=True)
        update_data["modified"] = datetime.now(timezone.utc)

        for key, value in update_data.items():
            setattr(item, key, value)

        await self.db.commit()
        await self.db.refresh(item)

        return {c.name: getattr(item, c.name) for c in item.__table__.columns}

    async def delete_invoice_item(self, item_uuid: str, user_id: str) -> None:
        """Delete an invoice item.

        Args:
            item_uuid: Invoice item UUID
            user_id: ID of user deleting the item

        Raises:
            InvoiceNotFoundError: If item not found
        """
        stmt = select(InvoiceItem).where(InvoiceItem.obj_uuid == item_uuid)
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise InvoiceNotFoundError(
                f"Invoice item with UUID {item_uuid} not found"
            )

        await self.db.delete(item)
        await self.db.commit()

    async def batch_approve_purchase_orders(
        self, po_uuids: List[str], user_id: str
    ) -> dict:
        """Approve multiple purchase orders.

        Args:
            po_uuids: List of purchase order UUIDs
            user_id: ID of user approving the POs

        Returns:
            Dict with success_count, failure_count, and results
        """
        results = []
        success_count = 0
        failure_count = 0

        for po_uuid in po_uuids:
            try:
                po = await self.approve_purchase_order(po_uuid, user_id)
                results.append({"po_uuid": po_uuid, "status": "success", "data": po})
                success_count += 1
            except Exception as e:
                results.append(
                    {
                        "po_uuid": po_uuid,
                        "status": "failed",
                        "error": str(e),
                    }
                )
                failure_count += 1

        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "results": results,
        }

    async def batch_delete_purchase_orders(
        self, po_uuids: List[str], user_id: str
    ) -> dict:
        """Delete multiple purchase orders (soft delete).

        Args:
            po_uuids: List of purchase order UUIDs
            user_id: ID of user deleting the POs

        Returns:
            Dict with success_count, failure_count, and results
        """
        results = []
        success_count = 0
        failure_count = 0

        for po_uuid in po_uuids:
            try:
                await self.delete_purchase_order(po_uuid, user_id)
                results.append({"po_uuid": po_uuid, "status": "success"})
                success_count += 1
            except Exception as e:
                results.append(
                    {
                        "po_uuid": po_uuid,
                        "status": "failed",
                        "error": str(e),
                    }
                )
                failure_count += 1

        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "results": results,
        }

    async def create_invoice_group(
        self, group_data: InvoiceGroupCreate, user_id: str
    ) -> dict:
        """Create a new invoice group.

        Args:
            group_data: Invoice group creation data
            user_id: ID of user creating the group

        Returns:
            Created invoice group dict
        """
        group_dict = group_data.model_dump(exclude_unset=True)
        group_dict["created"] = datetime.now(timezone.utc)
        group_dict["modified"] = datetime.now(timezone.utc)
        group_dict["created_by"] = user_id

        group = InvoiceGroup(**group_dict)
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)

        return {c.name: getattr(group, c.name) for c in group.__table__.columns}

    async def get_invoice_group(self, group_uuid: str) -> Optional[dict]:
        """Get an invoice group by UUID.

        Args:
            group_uuid: Invoice group UUID

        Returns:
            Invoice group dict if found, None otherwise
        """
        stmt = select(InvoiceGroup).where(
            InvoiceGroup.obj_uuid == group_uuid,
            InvoiceGroup.deleted != True
        )
        result = await self.db.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            return None

        return {c.name: getattr(group, c.name) for c in group.__table__.columns}

    async def get_invoice_group_or_404(self, group_uuid: str) -> dict:
        """Get an invoice group by UUID or raise 404.

        Args:
            group_uuid: Invoice group UUID

        Returns:
            Invoice group dict

        Raises:
            InvoiceGroupNotFoundError: If group not found
        """
        group = await self.get_invoice_group(group_uuid)
        if not group:
            raise InvoiceGroupNotFoundError(
                f"Invoice group with UUID {group_uuid} not found"
            )
        return group

    async def get_invoice_group_with_invoices(self, group_uuid: str) -> dict:
        """Get an invoice group with its invoices.

        Args:
            group_uuid: Invoice group UUID

        Returns:
            Invoice group dict with invoices list

        Raises:
            InvoiceGroupNotFoundError: If group not found
        """
        group = await self.get_invoice_group_or_404(group_uuid)

        # Get invoices in this group
        stmt = select(Invoice).where(
            Invoice.invoice_groupid == group["id"],
            Invoice.deleted != True
        )
        result = await self.db.execute(stmt)
        invoices = result.scalars().all()

        group["invoices"] = [
            {c.name: getattr(inv, c.name) for c in inv.__table__.columns}
            for inv in invoices
        ]

        return group

    async def update_invoice_group(
        self, group_uuid: str, group_data: InvoiceGroupUpdate, user_id: str
    ) -> dict:
        """Update an invoice group.

        Args:
            group_uuid: Invoice group UUID
            group_data: Invoice group update data
            user_id: ID of user updating the group

        Returns:
            Updated invoice group dict

        Raises:
            InvoiceGroupNotFoundError: If group not found
        """
        stmt = select(InvoiceGroup).where(
            InvoiceGroup.obj_uuid == group_uuid,
            InvoiceGroup.deleted != True
        )
        result = await self.db.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            raise InvoiceGroupNotFoundError(
                f"Invoice group with UUID {group_uuid} not found"
            )

        update_data = group_data.model_dump(exclude_unset=True)
        update_data["modified"] = datetime.now(timezone.utc)
        update_data["modified_by"] = user_id

        for key, value in update_data.items():
            setattr(group, key, value)

        await self.db.commit()
        await self.db.refresh(group)

        return {c.name: getattr(group, c.name) for c in group.__table__.columns}

    async def delete_invoice_group(self, group_uuid: str, user_id: str) -> None:
        """Delete an invoice group (soft delete).

        Args:
            group_uuid: Invoice group UUID
            user_id: ID of user deleting the group

        Raises:
            InvoiceGroupNotFoundError: If group not found
        """
        stmt = select(InvoiceGroup).where(
            InvoiceGroup.obj_uuid == group_uuid,
            InvoiceGroup.deleted != True
        )
        result = await self.db.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            raise InvoiceGroupNotFoundError(
                f"Invoice group with UUID {group_uuid} not found"
            )

        group.deleted = True
        group.modified = datetime.now(timezone.utc)
        group.modified_by = user_id
        await self.db.commit()

    async def add_invoice_to_group(
        self, group_uuid: str, invoice_uuid: str, user_id: str
    ) -> dict:
        """Add an invoice to an invoice group.

        Args:
            group_uuid: Invoice group UUID
            invoice_uuid: Invoice UUID to add
            user_id: ID of user performing the action

        Returns:
            Updated invoice group dict

        Raises:
            InvoiceGroupNotFoundError: If group not found
            InvoiceNotFoundError: If invoice not found
        """
        group = await self.get_invoice_group_or_404(group_uuid)

        # Verify invoice exists
        invoice_dict = await self.get_invoice(invoice_uuid)
        if not invoice_dict:
            raise InvoiceNotFoundError(f"Invoice with UUID {invoice_uuid} not found")

        # Update invoice to link to group
        stmt = select(Invoice).where(Invoice.obj_uuid == invoice_uuid)
        result = await self.db.execute(stmt)
        invoice_obj = result.scalar_one_or_none()

        if invoice_obj:
            invoice_obj.invoice_groupid = group["id"]
            invoice_obj.modified = datetime.now(timezone.utc)
            invoice_obj.modified_by = user_id
            await self.db.commit()

        return await self.get_invoice_group_with_invoices(group_uuid)

    async def remove_invoice_from_group(
        self, group_uuid: str, invoice_uuid: str, user_id: str
    ) -> dict:
        """Remove an invoice from an invoice group.

        Args:
            group_uuid: Invoice group UUID
            invoice_uuid: Invoice UUID to remove
            user_id: ID of user performing the action

        Returns:
            Updated invoice group dict

        Raises:
            InvoiceGroupNotFoundError: If group not found
            InvoiceNotFoundError: If invoice not found
        """
        await self.get_invoice_group_or_404(group_uuid)

        # Verify invoice exists
        invoice_dict = await self.get_invoice(invoice_uuid)
        if not invoice_dict:
            raise InvoiceNotFoundError(f"Invoice with UUID {invoice_uuid} not found")

        # Update invoice to remove group link
        stmt = select(Invoice).where(Invoice.obj_uuid == invoice_uuid)
        result = await self.db.execute(stmt)
        invoice_obj = result.scalar_one_or_none()

        if invoice_obj:
            invoice_obj.invoice_groupid = None
            invoice_obj.modified = datetime.now(timezone.utc)
            invoice_obj.modified_by = user_id
            await self.db.commit()

        return await self.get_invoice_group_with_invoices(group_uuid)

    async def list_invoice_groups(
        self,
        filters: InvoiceGroupFilterParams,
    ) -> tuple[List[dict], int]:
        """List invoice groups with filtering and pagination.

        Args:
            filters: Filter parameters

        Returns:
            Tuple of (invoice groups list, total count)
        """
        stmt = select(InvoiceGroup).where(InvoiceGroup.deleted != True)
        conditions = []

        # Apply filters
        if filters.status:
            conditions.append(InvoiceGroup.status == filters.status)

        if filters.companyid:
            conditions.append(InvoiceGroup.companyid == filters.companyid)

        if filters.invoice_date_from:
            conditions.append(InvoiceGroup.invoice_date >= filters.invoice_date_from)

        if filters.invoice_date_to:
            conditions.append(InvoiceGroup.invoice_date <= filters.invoice_date_to)

        if filters.due_date_from:
            conditions.append(InvoiceGroup.due_date >= filters.due_date_from)

        if filters.due_date_to:
            conditions.append(InvoiceGroup.due_date <= filters.due_date_to)

        if filters.currency:
            conditions.append(InvoiceGroup.currency == filters.currency)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Get total count before pagination
        count_stmt = select(func.count()).select_from(
            select(InvoiceGroup)
            .where(InvoiceGroup.deleted != True)
            .where(and_(*conditions) if conditions else True)
            .subquery()
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(InvoiceGroup, filters.sort_by, InvoiceGroup.invoice_date)
        if filters.sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.offset(offset).limit(filters.page_size)

        result = await self.db.execute(stmt)
        groups = result.scalars().all()

        # Convert to dicts
        groups_list = [
            {c.name: getattr(group, c.name) for c in group.__table__.columns}
            for group in groups
        ]

        return groups_list, total


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
    ) -> dict:
        """Create a new purchase order.

        Args:
            po_data: Purchase order creation data
            user_id: ID of user creating the PO

        Returns:
            Created purchase order dict with job_id
        """
        po_dict = po_data.model_dump(exclude_unset=True)
        po_dict["created"] = datetime.now(timezone.utc)
        po_dict["modified"] = datetime.now(timezone.utc)

        po = PurchaseOrder(**po_dict)
        self.db.add(po)
        await self.db.commit()
        await self.db.refresh(po)

        # Return enriched dict with job_id
        return await self.get_purchase_order(po.obj_uuid)

    async def get_purchase_order(self, po_uuid: str) -> Optional[dict]:
        """Get a purchase order by UUID with enriched job_id.

        Args:
            po_uuid: Purchase order UUID

        Returns:
            Purchase order dict with job_id if found, None otherwise
        """
        from sqlalchemy import Table, MetaData, Column, Integer, String, text

        # Define Job table for joining (manually, not autoload)
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
                PurchaseOrder,
                job_table.c.id.label("job_id"),
            )
            .outerjoin(job_table, PurchaseOrder.tp_job == job_table.c.obj_uuid)
            .where(
                PurchaseOrder.obj_uuid == po_uuid,
                PurchaseOrder.is_deleted != True
            )
        )
        result = await self.db.execute(stmt)
        row = result.first()

        if not row:
            return None

        po = row[0]
        job_id = row[1]

        # Convert PO model to dict and add job_id
        po_dict = {
            column.name: getattr(po, column.name)
            for column in PurchaseOrder.__table__.columns
        }
        po_dict["job_id"] = job_id

        return po_dict

    async def get_purchase_order_or_404(self, po_uuid: str) -> dict:
        """Get a purchase order by UUID or raise 404.

        Args:
            po_uuid: Purchase order UUID

        Returns:
            Purchase order dict with job_id

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
    ) -> dict:
        """Update a purchase order.

        Args:
            po_uuid: Purchase order UUID
            po_data: Purchase order update data
            user_id: ID of user updating the PO

        Returns:
            Updated purchase order dict with job_id

        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        # Get the actual PO model for updating (not enriched dict)
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.obj_uuid == po_uuid,
            PurchaseOrder.is_deleted != True
        )
        result = await self.db.execute(stmt)
        po = result.scalar_one_or_none()

        if not po:
            raise PurchaseOrderNotFoundError(
                f"Purchase order with UUID {po_uuid} not found"
            )

        update_data = po_data.model_dump(exclude_unset=True)
        update_data["modified"] = datetime.now(timezone.utc)

        # Validate status transition if status is being updated
        if "status" in update_data and po.status:
            validate_po_status_transition(po.status, update_data["status"])

        for key, value in update_data.items():
            setattr(po, key, value)

        await self.db.commit()
        await self.db.refresh(po)

        # Return enriched dict with job_id
        return await self.get_purchase_order(po_uuid)

    async def delete_purchase_order(self, po_uuid: str, user_id: str) -> None:
        """Delete a purchase order (soft delete).

        Args:
            po_uuid: Purchase order UUID
            user_id: ID of user deleting the PO

        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        # Get the actual PO model for updating (not enriched dict)
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.obj_uuid == po_uuid,
            PurchaseOrder.is_deleted != True
        )
        result = await self.db.execute(stmt)
        po = result.scalar_one_or_none()

        if not po:
            raise PurchaseOrderNotFoundError(
                f"Purchase order with UUID {po_uuid} not found"
            )

        po.is_deleted = True
        po.modified = datetime.now(timezone.utc)
        await self.db.commit()

    async def archive_purchase_order(self, po_uuid: str, user_id: str) -> dict:
        """Archive a purchase order.

        Args:
            po_uuid: Purchase order UUID
            user_id: ID of user archiving the PO

        Returns:
            Archived purchase order dict

        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.obj_uuid == po_uuid,
            PurchaseOrder.is_deleted != True
        )
        result = await self.db.execute(stmt)
        po = result.scalar_one_or_none()

        if not po:
            raise PurchaseOrderNotFoundError(
                f"Purchase order with UUID {po_uuid} not found"
            )

        po.is_deleted = True  # Use deleted flag for archiving
        po.status = "Archived"
        po.modified = datetime.now(timezone.utc)
        await self.db.commit()

        return await self.get_purchase_order(po_uuid)

    async def restore_purchase_order(self, po_uuid: str, user_id: str) -> dict:
        """Restore an archived purchase order.

        Args:
            po_uuid: Purchase order UUID
            user_id: ID of user restoring the PO

        Returns:
            Restored purchase order dict

        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        # Get PO even if deleted (archived)
        stmt = select(PurchaseOrder).where(PurchaseOrder.obj_uuid == po_uuid)
        result = await self.db.execute(stmt)
        po = result.scalar_one_or_none()

        if not po:
            raise PurchaseOrderNotFoundError(
                f"Purchase order with UUID {po_uuid} not found"
            )

        po.is_deleted = False
        if po.status == "Archived":
            po.status = "Pending"  # Restore to pending status
        po.modified = datetime.now(timezone.utc)
        await self.db.commit()

        return await self.get_purchase_order(po_uuid)

    async def approve_purchase_order(self, po_uuid: str, user_id: str) -> dict:
        """Approve a purchase order for payment.

        Args:
            po_uuid: Purchase order UUID
            user_id: ID of user approving the PO

        Returns:
            Approved purchase order dict with job_id

        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        # Get the actual PO model for updating (not enriched dict)
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.obj_uuid == po_uuid,
            PurchaseOrder.is_deleted != True
        )
        result = await self.db.execute(stmt)
        po = result.scalar_one_or_none()

        if not po:
            raise PurchaseOrderNotFoundError(
                f"Purchase order with UUID {po_uuid} not found"
            )

        # Validate status transition
        validate_po_status_transition(po.status or "Pending", "Approved")

        po.approvedforpayment = 1
        po.approveddate = datetime.now(timezone.utc)
        po.status = "Approved"
        po.modified = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(po)

        # Return enriched dict with job_id
        return await self.get_purchase_order(po_uuid)

    async def list_purchase_orders(
        self,
        filters: PurchaseOrderFilterParams,
    ) -> tuple[List[dict], int]:
        """List purchase orders with filtering and pagination.

        Args:
            filters: Filter parameters

        Returns:
            Tuple of (POs list with enriched data, total count)
        """
        from sqlalchemy import Table, MetaData, Column, Integer, String

        # Define Job table for joining (manually, not autoload)
        metadata = MetaData()
        job_table = Table(
            "obj_tp_job",
            metadata,
            Column("obj_uuid", String(36), primary_key=True),
            Column("id", Integer),
            schema="franchise"
        )

        # Create query with LEFT JOIN to get job_id
        stmt = (
            select(
                PurchaseOrder,
                job_table.c.id.label("job_id"),
            )
            .outerjoin(job_table, PurchaseOrder.tp_job == job_table.c.obj_uuid)
            .where(PurchaseOrder.is_deleted != True)
        )
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
        count_stmt = (
            select(func.count())
            .select_from(PurchaseOrder)
            .outerjoin(job_table, PurchaseOrder.tp_job == job_table.c.obj_uuid)
            .where(PurchaseOrder.is_deleted != True)
        )
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))

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
        rows = result.all()

        # Convert rows to dictionaries with enriched data
        pos_with_job_id = []
        for row in rows:
            po = row[0]
            job_id = row[1]

            # Convert PO model to dict and add job_id
            po_dict = {
                column.name: getattr(po, column.name)
                for column in PurchaseOrder.__table__.columns
            }
            po_dict["job_id"] = job_id
            pos_with_job_id.append(po_dict)

        return pos_with_job_id, total

    async def list_po_milestones(self, po_uuid: str) -> List[dict]:
        """List all milestones for a purchase order.

        Args:
            po_uuid: Purchase order UUID

        Returns:
            List of PO milestone dicts
        """
        stmt = (
            select(POMilestone)
            .where(POMilestone.tp_purchaseorder == po_uuid)
            .order_by(POMilestone.milestone)
        )
        result = await self.db.execute(stmt)
        milestones = result.scalars().all()

        return [
            {c.name: getattr(milestone, c.name) for c in milestone.__table__.columns}
            for milestone in milestones
        ]

    async def create_po_milestone(
        self, po_uuid: str, milestone_data: dict, user_id: str
    ) -> dict:
        """Create a new PO milestone.

        Args:
            po_uuid: Purchase order UUID
            milestone_data: Milestone creation data (milestone percentage, notes, etc.)
            user_id: ID of user creating the milestone

        Returns:
            Created PO milestone dict
        """
        # Verify PO exists
        await self.get_purchase_order_or_404(po_uuid)

        milestone_dict = milestone_data.copy()
        milestone_dict["tp_purchaseorder"] = po_uuid
        milestone_dict["created"] = datetime.now(timezone.utc)
        milestone_dict["modified"] = datetime.now(timezone.utc)

        milestone = POMilestone(**milestone_dict)
        self.db.add(milestone)
        await self.db.commit()
        await self.db.refresh(milestone)

        return {c.name: getattr(milestone, c.name) for c in milestone.__table__.columns}

    async def get_po_milestone(self, milestone_uuid: str) -> Optional[dict]:
        """Get a PO milestone by UUID.

        Args:
            milestone_uuid: PO milestone UUID

        Returns:
            PO milestone dict if found, None otherwise
        """
        stmt = select(POMilestone).where(POMilestone.obj_uuid == milestone_uuid)
        result = await self.db.execute(stmt)
        milestone = result.scalar_one_or_none()

        if not milestone:
            return None

        return {c.name: getattr(milestone, c.name) for c in milestone.__table__.columns}

    async def update_po_milestone(
        self, milestone_uuid: str, milestone_data: dict, user_id: str
    ) -> dict:
        """Update a PO milestone.

        Args:
            milestone_uuid: PO milestone UUID
            milestone_data: Milestone update data
            user_id: ID of user updating the milestone

        Returns:
            Updated PO milestone dict

        Raises:
            PurchaseOrderNotFoundError: If milestone not found
        """
        stmt = select(POMilestone).where(POMilestone.obj_uuid == milestone_uuid)
        result = await self.db.execute(stmt)
        milestone = result.scalar_one_or_none()

        if not milestone:
            raise PurchaseOrderNotFoundError(
                f"PO milestone with UUID {milestone_uuid} not found"
            )

        update_data = milestone_data.copy()
        update_data["modified"] = datetime.now(timezone.utc)

        for key, value in update_data.items():
            setattr(milestone, key, value)

        await self.db.commit()
        await self.db.refresh(milestone)

        return {c.name: getattr(milestone, c.name) for c in milestone.__table__.columns}
