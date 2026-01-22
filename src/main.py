from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import buglog

try:
    from elasticapm.contrib.starlette import ElasticAPM, make_apm_client
    ELASTIC_APM_AVAILABLE = True
except ImportError:
    ELASTIC_APM_AVAILABLE = False

from .config import Environment, config, domains
from .example.router import router as example_router
from .health.router import router as health_router
from .invoices.router import router as invoices_router
from .middleware import custom_validation_exception_handler


# Configure BugLog
buglog.init(
    listener=config.buglog_listener_url,
    app_name="Invoice/Purchase Order Service API",
    # hostname=domains.,  # TODO
)


# Configure FastAPI
app = FastAPI(
    title="Invoice/Purchase Order Service API",
    description="Microservice for managing invoices and purchase orders",
    docs_url="/docs" if config.environment != Environment.production else None,
    redoc_url="/redoc" if config.environment != Environment.production else None,
)

# CORS origins are configured via CORS_ORIGINS environment variable
# Defaults to localhost and production/staging URLs if not set
# Example: CORS_ORIGINS="http://localhost:13001,http://10.135.60.85:13001,https://franchise.strakergroup.com"
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After", "X-Ratelimit-Limit"],
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(example_router, prefix="/example", tags=["example"])
app.include_router(invoices_router, prefix="/v1", tags=["invoices"])

# Configure Elastic APM
if config.elastic_apm_server_url and ELASTIC_APM_AVAILABLE:
    apm = make_apm_client(
        {
            "SERVICE_NAME": "invoice-purchase-order-service-api",
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
