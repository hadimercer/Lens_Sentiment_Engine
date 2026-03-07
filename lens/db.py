"""Database connection helpers."""

from __future__ import annotations

from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import get_settings


@contextmanager
def get_connection():
    """Open a short-lived PostgreSQL connection for the current request."""
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    connection = psycopg2.connect(
        settings.database_url,
        connect_timeout=settings.db_connect_timeout,
        cursor_factory=RealDictCursor,
    )
    try:
        yield connection
    finally:
        connection.close()
