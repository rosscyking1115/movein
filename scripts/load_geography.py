"""Load the normalized national ONSPD postcode lookup into the DuckDB warehouse.

Reads `data/raw/ref_onspd_normalized.csv` (produced by
`scripts/prepare_onspd_seed.py`) and (re)builds `raw_geo.onspd_postcodes`.
Idempotent — drops and recreates the table.

This is the real, national geography source. The committed
`seeds/ref_onspd_sample.csv` stays as the small CI fixture; build dbt against
the real lookup with:

    python scripts/load_geography.py
    dbt build --vars 'geo_source: onspd'

If the normalized file is absent this is a no-op (exit 0), so CI and fresh
clones that only have the committed fixture are unaffected.

Note (kit lesson L4): on Windows only one process can hold the warehouse open
in write mode — close any Streamlit dev server before running this.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
NORMALIZED = ROOT / "data" / "raw" / "ref_onspd_normalized.csv"
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"


def main() -> int:
    if not NORMALIZED.exists():
        print(
            f"No normalized lookup at {NORMALIZED}.\n"
            f"Run scripts/prepare_onspd_seed.py first, or build with the "
            f"committed fixture (default geo_source=fixture).",
            file=sys.stderr,
        )
        return 0

    print(f"Loading {NORMALIZED.name} into {WAREHOUSE}")
    con = duckdb.connect(str(WAREHOUSE))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw_geo")
        con.execute("DROP TABLE IF EXISTS raw_geo.onspd_postcodes")
        con.execute(
            f"""
            CREATE TABLE raw_geo.onspd_postcodes AS
            SELECT * FROM read_csv_auto('{NORMALIZED.as_posix()}', header=true)
            """
        )
        rowcount = con.execute(
            "SELECT count(*) FROM raw_geo.onspd_postcodes"
        ).fetchone()[0]
        mapped = con.execute(
            "SELECT count(*) FROM raw_geo.onspd_postcodes WHERE area_id IS NOT NULL"
        ).fetchone()[0]
    finally:
        con.close()

    print(f"Loaded {rowcount:,} postcodes ({mapped:,} with an MSOA area_id).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
