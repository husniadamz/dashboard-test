"""Create the PACED KPI sample database and fill it with sample data.

Run from the project root:

    python -m app.seed

Requires CASEMIXPAY_DB_USER (and CASEMIXPAY_DB_PASSWORD if the account has one).
Writes only to PACED_SAMPLE_DB_NAME (default paced_dashboard), never to the live database.
Safe to re-run: the KPI tables are dropped and reloaded. User data is read live from
casemix and is not seeded.
"""

from __future__ import annotations

from sqlalchemy import text

from app.data import make_monthly_metrics, make_region_metrics
from app.db import get_engine, sample_database_name, server_engine

SCHEMA = [
    """
    CREATE TABLE kpi_monthly_metrics (
        month CHAR(7) PRIMARY KEY,
        revenue DOUBLE NOT NULL,
        orders INT NOT NULL,
        new_customers INT NOT NULL,
        churn_rate DOUBLE NOT NULL,
        nps DOUBLE NOT NULL
    )
    """,
    """
    CREATE TABLE kpi_region_metrics (
        region VARCHAR(20) PRIMARY KEY,
        revenue DOUBLE NOT NULL,
        target DOUBLE NOT NULL
    )
    """,
]

TABLES = [
    "kpi_region_metrics",
    "kpi_monthly_metrics",
]


def create_database() -> None:
    name = sample_database_name()
    engine = server_engine()
    with engine.begin() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    engine.dispose()


def seed() -> dict[str, int]:
    engine = get_engine(sample_database_name())
    with engine.begin() as conn:
        for table in TABLES:
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
        for ddl in SCHEMA:
            conn.execute(text(ddl))

    datasets = {
        "kpi_monthly_metrics": make_monthly_metrics(),
        "kpi_region_metrics": make_region_metrics(),
    }
    counts = {}
    for table, df in datasets.items():
        df.to_sql(table, engine, if_exists="append", index=False)
        counts[table] = len(df)
    return counts


def main() -> None:
    create_database()
    counts = seed()
    print(f"Seeded database '{sample_database_name()}':")
    for table, n in counts.items():
        print(f"  {table}: {n} rows")


if __name__ == "__main__":
    main()
