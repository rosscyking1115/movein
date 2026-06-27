"""Load the normalized police street-level crime into the DuckDB warehouse.

Reads `data/raw/ref_crime_normalized.csv` (produced by
`scripts/prepare_crime_seed.py`) and (re)builds `raw_police.street_crime`.
Idempotent. The committed `seeds/ref_crime_sample.csv` stays as the CI fixture;
build against the real crimes with:

    python scripts/prepare_crime_seed.py path/to/police-bulk.zip
    python scripts/load_crime.py
    dbt build --vars 'crime_source: bulk'

If the normalized file is absent this is a no-op (exit 0), so CI and fresh
clones that only have the committed fixture are unaffected.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
NORMALIZED = ROOT / "data" / "raw" / "ref_crime_normalized.csv"
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"


def main() -> int:
    if not NORMALIZED.exists():
        print(
            f"No normalized crime file at {NORMALIZED}.\n"
            f"Run scripts/prepare_crime_seed.py first, or build with the committed "
            f"fixture (default crime_source=fixture).",
            file=sys.stderr,
        )
        return 0

    print(f"Loading {NORMALIZED.name} into {WAREHOUSE}")
    con = duckdb.connect(str(WAREHOUSE))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw_police")
        con.execute("DROP TABLE IF EXISTS raw_police.street_crime")
        con.execute(
            f"""
            CREATE TABLE raw_police.street_crime AS
            SELECT * FROM read_csv_auto('{NORMALIZED.as_posix()}', header=true)
            """
        )
        rowcount = con.execute("SELECT count(*) FROM raw_police.street_crime").fetchone()[0]
    finally:
        con.close()

    print(f"Loaded {rowcount:,} crime rows into raw_police.street_crime.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
