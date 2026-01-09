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
    # Replace the driver with the async one
    url = str(sync_engine.url).replace("mysqlconnector", "aiomysql")
    # Ensure it starts with mysql+aiomysql://
    if "mysql://" in url and "aiomysql" not in url:
         url = url.replace("mysql://", "mysql+aiomysql://")

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
