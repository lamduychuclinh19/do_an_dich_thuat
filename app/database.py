import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


load_dotenv()


db_server = os.getenv("DB_SERVER")
db_name = os.getenv("DB_NAME")
db_driver = os.getenv("DB_DRIVER")


if not db_server or not db_name or not db_driver:
    raise RuntimeError(
        "Thiếu DB_SERVER, DB_NAME hoặc DB_DRIVER trong file .env"
    )


connection_string = (
    f"DRIVER={{{db_driver}}};"
    f"SERVER={db_server};"
    f"DATABASE={db_name};"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "LongAsMax=Yes;"
)


connection_url = URL.create(
    "mssql+pyodbc",
    query={"odbc_connect": connection_string},
)


engine = create_engine(
    connection_url,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()


def test_database_connection() -> str:
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT DB_NAME()")
        ).scalar_one()

        return database_name