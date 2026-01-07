from functools import cache
from random import randrange

from .schemas import Example


@cache
def mock_data():
    return [Example(uuid=str(i + 1), value=randrange(100)) for i in range(100)]


def get_example_data_paginated(page: int, page_size: int):
    data = mock_data()
    start = (page - 1) * page_size
    end = start + page_size
    paginated_data = data[start:end]
    return paginated_data, len(data)


def get_example_data(uuid: str):
    data = mock_data()
    for e in data:
        if e.uuid == uuid:
            return e
    return None
