"""Load the per-MSOA amenity-access roll-up into the DuckDB warehouse.

Reads `data/raw/ref_amenity_access.csv` (produced by
`scripts/prepare_amenity_access.py`) and (re)builds
`raw_amenities.area_access`. Idempotent. The committed
`seeds/ref_amenity_access_sample.csv` stays as the CI fixture; build against the
real roll-up with:

    python scripts/prepare_amenity_access.py path/to/great-britain-latest.osm.pbf
    python scripts/load_amenities.py
    dbt build --vars 'amenities_source: computed'

If the file is absent this is a no-op (exit 0), so CI and fresh clones that only
have the committed fixture are unaffected.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "raw" / "ref_amenity_access.csv"
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"


def main() -> int:
    if not SOURCE.exists():
        print(
            f"No amenity-access roll-up at {SOURCE}.\n"
            f"Run scripts/prepare_amenity_access.py first, or build with the "
            f"committed fixture (default amenities_source=fixture).",
            file=sys.stderr,
        )
        return 0

    print(f"Loading {SOURCE.name} into {WAREHOUSE}")
    con = duckdb.connect(str(WAREHOUSE))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw_amenities")
        con.execute("DROP TABLE IF EXISTS raw_amenities.area_access")
        con.execute(
            f"""
            CREATE TABLE raw_amenities.area_access AS
            SELECT * FROM read_csv_auto('{SOURCE.as_posix()}', header=true)
            """
        )
        rowcount = con.execute("SELECT count(*) FROM raw_amenities.area_access").fetchone()[0]
    finally:
        con.close()

    print(f"Loaded {rowcount:,} MSOA amenity-access rows into raw_amenities.area_access.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
