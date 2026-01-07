from fastapi import (
    APIRouter,
    HTTPException,
)

from ..pagination import paginate, validate_pagination
from .schemas import (
    GetExampleResponse,
    GetExamplesResponse,
)
from .service import (
    get_example_data,
    get_example_data_paginated,
)


router = APIRouter()


@router.get("")
async def get_examples_endpoint(
    page: int = 1,
    page_size: int = 10,
) -> GetExamplesResponse:
    pagination = validate_pagination(page, page_size)
    examples, total = get_example_data_paginated(page, page_size)
    return GetExamplesResponse(data=examples, pagination=paginate(pagination, total))


@router.get("/{uuid}")
async def get_example_endpoint(uuid: str) -> GetExampleResponse:
    example = get_example_data(uuid)
    if not example:
        raise HTTPException(404)
    return GetExampleResponse(data=example)
