from fastapi import Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError


async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom validation exception handler. Returns a 400 response instead of a
    422 response.
    """
    response = await request_validation_exception_handler(request, exc)
    response.status_code = 400
    return response
