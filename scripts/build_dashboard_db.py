"""Build a slim DuckDB containing only the rpt_* tables for Streamlit Cloud.

The full warehouse (data/warehouse.duckdb) is ~200MB with 4M+ fct rows
and 988K dim_postcode rows. The dashboard only needs the three reporting
marts (~700 rows total) — committing those alone keeps the file small
enough for git (<1MB), well under GitHub's 100MB hard limit (kit lesson L13).

This script is idempotent: drops + recreates data/dashboard.duckdb on every
run. Re-run it whenever the upstream warehouse refreshes.

Usage:
    python scripts/build_dashboard_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DB = ROOT / "data" / "warehouse.duckdb"
TARGET_DB = ROOT / "data" / "dashboard.duckdb"

# Reporting marts that the Streamlit app consumes. Each one is read-only
# at view time; rebuild this DB to refresh.
TABLES_TO_EXPORT = [
    ("main_analytics", "rpt_price_yoy_by_region"),
    ("main_analytics", "rpt_top_postcodes_by_volume"),
    ("main_analytics", "rpt_new_build_premium"),
]


def main() -> int:
    if not SOURCE_DB.exists():
        print(
            f"Source warehouse not found at {SOURCE_DB}.\n"
            f"Run `dbt build` first to populate the full warehouse.",
            file=sys.stderr,
        )
        return 1

    # Drop + recreate target — full rebuild every time
    if TARGET_DB.exists():
        TARGET_DB.unlink()
        print(f"Removed existing {TARGET_DB.name}")

    print(f"Building {TARGET_DB.name} from {SOURCE_DB.name}...")
    target = duckdb.connect(str(TARGET_DB))

    # ATTACH the full warehouse read-only so we can SELECT from it directly
    target.execute(f"ATTACH '{SOURCE_DB.as_posix()}' AS source (READ_ONLY)")

    target.execute("CREATE SCHEMA IF NOT EXISTS analytics")

    total_rows = 0
    for source_schema, table in TABLES_TO_EXPORT:
        target.execute(
            f"""
            CREATE TABLE analytics.{table} AS
            SELECT * FROM source.{source_schema}.{table}
            """
        )
        rowcount = target.execute(
            f"SELECT count(*) FROM analytics.{table}"
        ).fetchone()[0]
        print(f"  analytics.{table:<32}  {rowcount:>6,} rows")
        total_rows += rowcount

    target.execute("DETACH source")
    target.close()

    size_kb = TARGET_DB.stat().st_size / 1024
    print(f"\nDone. {total_rows:,} rows total, {size_kb:.1f} KB on disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
