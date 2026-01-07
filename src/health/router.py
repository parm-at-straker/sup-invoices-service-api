import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Response

from ..config import Environment, config
from ..database import engines
from ..redis import redis_conn
from .schemas import HealthCheckResponse


router = APIRouter()


@router.get("")
async def health_check(response: Response, password: str | None = None) -> HealthCheckResponse:
    if (
        config.environment == Environment.production
        and password != config.health_check_password.get_secret_value()
    ):
        raise HTTPException(401, "Not authorised")

    info: dict[str, Any] = {}
    errors: dict[str, Any] = {}

    await asyncio.gather(
        _check_database(errors),
        _check_redis(errors),
    )

    message = "There are some issues" if len(errors) else "OK"

    if errors:
        response.status_code = 500
        logging.warning(
            json.dumps(
                {
                    "message": message,
                    "environment": config.environment.value,
                    "info": info,
                    "errors": errors,
                },
                indent=4,
            )
        )

    return HealthCheckResponse(
        message=message, environment=config.environment.value, info=info, errors=errors
    )


async def _check_database(errors: dict[str, Any]) -> None:
    try:
        await engines.ping_all_async()
    except Exception as e:
        errors["database"] = str(e)


async def _check_redis(errors: dict[str, Any]) -> None:
    try:
        await redis_conn.ping()
    except Exception as e:
        errors["redis"] = str(e)
