import databases
from os import environ


DB_USER = environ.get("DB_USER", "fastapi_user")
DB_PASSWORD = environ.get("DB_PASSWORD", "fastapi")
DB_HOST = environ.get("DB_HOST", "localhost")

TESTING = environ.get("TESTING", "TESTING")

if TESTING:
    DB_NAME = "cats_db"
    TEST_SQLALCHEMY_DATABASE_URL = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    )
    database = databases.Database(TEST_SQLALCHEMY_DATABASE_URL)
else:
    DB_NAME = "cats_db"
    SQLALCHEMY_DATABASE_URL = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    )
    database = databases.Database(SQLALCHEMY_DATABASE_URL)
