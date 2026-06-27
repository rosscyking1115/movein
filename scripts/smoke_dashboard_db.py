"""Smoke-test the Streamlit dashboard DuckDB extract.

This catches drift between the dbt reporting marts, the slim
`data/dashboard.duckdb` file, and the Streamlit load helpers before a
broken dashboard can deploy.

Usage:
    python scripts/smoke_dashboard_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DB = ROOT / "data" / "dashboard.duckdb"

REQUIRED_TABLES = {
    "rpt_price_yoy_by_region": {
        "region",
        "transferred_year",
        "sales_count",
        "mean_price_gbp",
        "median_price_gbp",
        "p10_price_gbp",
        "p90_price_gbp",
        "prior_year_median_price_gbp",
        "prior_year_mean_price_gbp",
        "median_yoy_pct",
        "mean_yoy_pct",
    },
    "rpt_top_postcodes_by_volume": {
        "postcode_area",
        "region",
        "transferred_year",
        "sales_count",
        "mean_price_gbp",
        "median_price_gbp",
        "rank_within_year",
    },
    "rpt_new_build_premium": {
        "region",
        "transferred_year",
        "new_build_count",
        "existing_count",
        "new_build_mean_price_gbp",
        "existing_mean_price_gbp",
        "new_build_median_price_gbp",
        "existing_median_price_gbp",
        "premium_pct",
    },
}


def fail(message: str) -> int:
    print(f"[fail] {message}", file=sys.stderr)
    return 1


def main() -> int:
    if not DASHBOARD_DB.exists():
        return fail(f"Dashboard database not found at {DASHBOARD_DB}")

    con = duckdb.connect(str(DASHBOARD_DB), read_only=True)
    try:
        tables = {
            row[0]
            for row in con.execute(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'analytics'
                """
            ).fetchall()
        }

        missing_tables = sorted(set(REQUIRED_TABLES) - tables)
        if missing_tables:
            return fail(f"Missing analytics table(s): {', '.join(missing_tables)}")

        total_rows = 0
        for table, required_columns in REQUIRED_TABLES.items():
            columns = {
                row[0]
                for row in con.execute(
                    """
                    select column_name
                    from information_schema.columns
                    where table_schema = 'analytics'
                      and table_name = ?
                    """,
                    [table],
                ).fetchall()
            }
            missing_columns = sorted(required_columns - columns)
            if missing_columns:
                return fail(
                    f"analytics.{table} missing column(s): "
                    f"{', '.join(missing_columns)}"
                )

            rowcount = con.execute(
                f"select count(*) from analytics.{table}"
            ).fetchone()[0]
            if rowcount == 0:
                return fail(f"analytics.{table} has zero rows")

            null_years = con.execute(
                f"""
                select count(*)
                from analytics.{table}
                where transferred_year is null
                """
            ).fetchone()[0]
            if null_years:
                return fail(f"analytics.{table} has NULL transferred_year values")

            print(f"[ok] analytics.{table}: {rowcount:,} rows")
            total_rows += rowcount
    finally:
        con.close()

    print(f"[ok] Dashboard database smoke test passed ({total_rows:,} rows total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
