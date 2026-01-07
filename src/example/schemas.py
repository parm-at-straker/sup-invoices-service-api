from pydantic import BaseModel

from ..pagination import Pagination


class Example(BaseModel):
    uuid: str
    value: int


class GetExamplesResponse(BaseModel):
    data: list[Example]
    pagination: Pagination


class GetExampleResponse(BaseModel):
    data: Example
