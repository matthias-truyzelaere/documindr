"""Database connection pooling configuration."""

from urllib.parse import quote_plus

from psycopg_pool import ConnectionPool

from app.core.config import get_settings

settings = get_settings()

if not all(
    [
        settings.postgres_user,
        settings.postgres_password,
        settings.postgres_host,
        settings.postgres_port,
        settings.postgres_db,
    ]
):
    raise RuntimeError("PostgreSQL environment variables are not fully set")

user = quote_plus(settings.postgres_user)
password = quote_plus(settings.postgres_password)
host = settings.postgres_host
port = settings.postgres_port
db = quote_plus(settings.postgres_db)

DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}"

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=10,
    timeout=10,
    open=True,
)


def close_pool():
    """Close all connections in the pool during shutdown."""
    global pool
    if pool:
        pool.close()
