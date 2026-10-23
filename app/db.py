"""MySQL connections for the PACED dashboard.

Live data is read from the `casemix` database. Settings come from environment
variables; nothing sensitive is stored in code:

    CASEMIXPAY_DB_HOST      default 127.0.0.1
    CASEMIXPAY_DB_PORT      default 3306
    CASEMIXPAY_DB_NAME      default casemix (live data, read-only use)
    CASEMIXPAY_DB_USER      required
    CASEMIXPAY_DB_PASSWORD  optional (empty when unset)
    PACED_SAMPLE_DB_NAME    default paced_dashboard (sample tables written by app/seed.py)
"""

from __future__ import annotations

import os
from functools import lru_cache
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DEFAULT_DB_NAME = "casemix"
DEFAULT_SAMPLE_DB_NAME = "paced_dashboard"


def _settings() -> tuple[str, str, str, str, str]:
    user = os.environ.get("CASEMIXPAY_DB_USER")
    if not user:
        raise RuntimeError("Set the CASEMIXPAY_DB_USER environment variable.")
    password = os.environ.get("CASEMIXPAY_DB_PASSWORD", "")
    host = os.environ.get("CASEMIXPAY_DB_HOST", "127.0.0.1")
    port = os.environ.get("CASEMIXPAY_DB_PORT", "3306")
    name = os.environ.get("CASEMIXPAY_DB_NAME", DEFAULT_DB_NAME)
    return user, password, host, port, name


def _url(database: str | None) -> str:
    user, password, host, port, _ = _settings()
    path = database or ""
    return f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{path}?charset=utf8mb4"


def database_name() -> str:
    """Live database (casemix) that the dashboard reads from."""
    return _settings()[4]


def sample_database_name() -> str:
    """Database holding the sample KPI tables. Kept separate from the live database."""
    return os.environ.get("PACED_SAMPLE_DB_NAME", DEFAULT_SAMPLE_DB_NAME)


def server_engine() -> Engine:
    """Engine without a default database, used to create the sample database."""
    return create_engine(_url(None), pool_pre_ping=True)


@lru_cache(maxsize=4)
def _engine_for(name: str) -> Engine:
    return create_engine(_url(name), pool_pre_ping=True, pool_recycle=3600)


def get_engine(database: str | None = None) -> Engine:
    return _engine_for(database or database_name())


def read_sql(query: str, database: str | None = None) -> pd.DataFrame:
    with get_engine(database).connect() as conn:
        return pd.read_sql(text(query), conn)


def check_connection() -> dict[str, str]:
    """Return the server version and current database name, or raise."""
    with get_engine().connect() as conn:
        row = conn.execute(text("SELECT VERSION() AS version, DATABASE() AS db")).one()
        return {"version": row.version, "database": row.db}
