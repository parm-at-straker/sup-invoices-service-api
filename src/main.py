from elasticapm.contrib.starlette import ElasticAPM, make_apm_client
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import buglog

from .config import Environment, config, domains
from .example.router import router as example_router
from .health.router import router as health_router
from .middleware import custom_validation_exception_handler


# Configure BugLog
buglog.init(
    listener=config.buglog_listener_url,
    app_name="API",  # TODO
    # hostname=domains.,  # TODO
)


# Configure FastAPI
app = FastAPI(
    title="API",
    description="",
    docs_url="/docs" if config.environment != Environment.production else None,
    redoc_url="/redoc" if config.environment != Environment.production else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After", "X-Ratelimit-Limit"],
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(example_router, prefix="/example", tags=["example"])

# Configure Elastic APM
if config.elastic_apm_server_url:
    apm = make_apm_client(
        {
            "SERVICE_NAME": "",  # TODO
            "SERVER_URL": config.elastic_apm_server_url,
            "ENVIRONMENT": config.environment.value,
            "TRANSACTION_IGNORE_URLS": ["/", "/health"],
            "TRANSACTIONS_IGNORE_PATTERNS": ["^OPTIONS ", "/health"],
        }
    )
    app.add_middleware(ElasticAPM, client=apm)

# Use 400 instead of 422 for validation errors
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)  # type: ignore


@app.get("/")
async def index():
    return {"message": "OK"}
