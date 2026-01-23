"""Sales Order service dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..invoices.dependencies import get_franchise_db
from .service import SalesOrderService


def get_sales_order_service(
    db: AsyncSession = Depends(get_franchise_db),
) -> SalesOrderService:
    """Get sales order service instance.

    Args:
        db: Database session

    Returns:
        SalesOrderService instance
    """
    return SalesOrderService(db)
