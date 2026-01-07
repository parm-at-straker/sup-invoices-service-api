from typing import Any, Literal

from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    message: str
    environment: Literal["local", "uat", "dev", "production"]
    info: dict[str, Any]
    errors: dict[str, Any]
