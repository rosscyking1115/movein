"""Load Land Registry Parquet files into the DuckDB warehouse.

Reads every `pp-*.parquet` under `data/raw/` and (re)builds the table
`raw_landreg.transactions` in `data/warehouse.duckdb`. Idempotent — drops and
recreates the table, so re-running after an extra year has been downloaded
gives you a consistent, deduplicated view.

Usage:
    python scripts/load_to_duckdb.py

Note (kit lesson L4): on Windows, only one process can hold the warehouse
file open in write mode. Make sure no Streamlit dev server is connected
before running this script.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"


def main() -> int:
    parquet_files = sorted(RAW_DIR.glob("pp-*.parquet"))
    if not parquet_files:
        print(
            f"No Parquet files in {RAW_DIR}.\n"
            f"Run `python scripts/download_raw.py` first.",
            file=sys.stderr,
        )
        return 1

    total_size_mb = sum(p.stat().st_size for p in parquet_files) / 1024 / 1024
    print(f"Found {len(parquet_files)} Parquet file(s) — {total_size_mb:.1f} MB total:")
    for p in parquet_files:
        size_mb = p.stat().st_size / 1024 / 1024
        print(f"  - {p.name} ({size_mb:.1f} MB)")
    print()

    print(f"Loading into {WAREHOUSE}")
    con = duckdb.connect(str(WAREHOUSE))

    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw_landreg")
        con.execute("DROP TABLE IF EXISTS raw_landreg.transactions")

        # DuckDB's read_parquet accepts a glob pattern. Forward slashes work
        # cross-platform inside DuckDB strings, so normalise.
        glob_pattern = (RAW_DIR / "pp-*.parquet").as_posix()
        con.execute(
            f"""
            CREATE TABLE raw_landreg.transactions AS
            SELECT * FROM read_parquet('{glob_pattern}')
            """
        )

        rowcount = con.execute(
            "SELECT count(*) FROM raw_landreg.transactions"
        ).fetchone()[0]
        min_date, max_date = con.execute(
            """
            SELECT min(date_of_transfer), max(date_of_transfer)
            FROM raw_landreg.transactions
            """
        ).fetchone()
    finally:
        con.close()

    print(f"\nLoaded {rowcount:,} rows into raw_landreg.transactions")
    print(f"Date range: {min_date} → {max_date}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
