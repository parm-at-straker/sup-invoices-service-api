from straker_utils.sql import DBEnginePool


engines = DBEnginePool(
    (
        "sitemanager",
        "sitemanager_readonly",
    ),
    dbapi="mysqlconnector",
    # echo=True,  # Uncomment to debug SQL queries
)
