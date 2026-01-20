from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from straker_utils.sql import DBEnginePool


engines = DBEnginePool(
    (
        "sitemanager",
        "sitemanager_readonly",
        "franchise",
        "franchise_readonly",
    ),
    dbapi="mysqlconnector",
    # echo=True,  # Uncomment to debug SQL queries
)


def get_async_engine(db_name: str):
    """Create an async engine from the sync engine URL."""
    sync_engine = engines[db_name]
    # Get the URL object to access the real password (not masked)
    url_obj = sync_engine.url
    # Build the async URL with the actual password
    url = f"mysql+aiomysql://{url_obj.username}:{url_obj.password}@{url_obj.host}:{url_obj.port}/{url_obj.database}"

    return create_async_engine(url, echo=False)


# Initialize async engines
async_engines = {
    "franchise": get_async_engine("franchise"),
    "franchise_readonly": get_async_engine("franchise_readonly"),
}

# Create session factories
AsyncFranchiseSessionLocal = async_sessionmaker(
    bind=async_engines["franchise"],
    class_=AsyncSession,
    expire_on_commit=False,
)

AsyncFranchiseReadonlySessionLocal = async_sessionmaker(
    bind=async_engines["franchise_readonly"],
    class_=AsyncSession,
    expire_on_commit=False,
)
