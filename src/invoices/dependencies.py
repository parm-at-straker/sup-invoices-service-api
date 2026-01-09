"""Invoice and Purchase Order service dependencies."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncFranchiseSessionLocal, AsyncFranchiseReadonlySessionLocal
from .service import InvoiceService, PurchaseOrderService


async def get_franchise_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for franchise database.

    Yields:
        Async Database session
    """
    async with AsyncFranchiseSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_franchise_readonly_db() -> AsyncGenerator[AsyncSession, None]:
    """Get read-only database session for franchise database.

    Yields:
        Read-only Async Database session
    """
    async with AsyncFranchiseReadonlySessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_invoice_service(
    db: AsyncSession = Depends(get_franchise_db),
) -> InvoiceService:
    """Get invoice service instance.

    Args:
        db: Database session

    Returns:
        InvoiceService instance
    """
    return InvoiceService(db)


def get_purchase_order_service(
    db: AsyncSession = Depends(get_franchise_db),
) -> PurchaseOrderService:
    """Get purchase order service instance.

    Args:
        db: Database session

    Returns:
        PurchaseOrderService instance
    """
    return PurchaseOrderService(db)
