from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError


class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    total: int = 1
    total_pages: int = 1


def validate_pagination(page: int, page_size: int):
    """Validates the pagination request values and returns the pagination
    settings. Raise an `HTTPException` if the pagination is not valid, e.g.
    negative values.

    Args:
        page (int): The page number.
        page_size (int): The number of items per page.

    Raises:
        HTTPException: The page or page_size values are not valid.

    Returns:
        Pagination: The validated pagination settings.
    """
    try:
        return Pagination(page=page, page_size=page_size)
    except ValidationError as e:
        raise HTTPException(400, detail=e.errors()) from e


def paginate(pagination: Pagination, total: int) -> Pagination:
    """Calculates the total pages from the pagination settings and total items.

    Args:
        pagination (Pagination): The pagination settings.
        total (int): The total number of items.

    Returns:
        Pagination: Pagination with total items and pages.
    """
    return Pagination(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
        total_pages=total // pagination.page_size + (total % pagination.page_size > 0),
    )
