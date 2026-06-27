"""Load the per-MSOA constraint roll-up into the DuckDB warehouse.

Reads `data/raw/ref_area_constraints.csv` (produced by
`scripts/prepare_area_constraints.py`) and (re)builds
`raw_constraints.area_constraints`. Idempotent. The committed
`seeds/ref_area_constraints_sample.csv` stays as the CI fixture; build against
the real roll-up with:

    python scripts/prepare_area_constraints.py path/to/planning_csv_dir
    python scripts/load_constraints.py
    dbt build --vars 'constraints_source: computed'

If the file is absent this is a no-op (exit 0), so CI and fresh clones that only
have the committed fixture are unaffected.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "raw" / "ref_area_constraints.csv"
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"


def main() -> int:
    if not SOURCE.exists():
        print(
            f"No constraint roll-up at {SOURCE}.\n"
            f"Run scripts/prepare_area_constraints.py first, or build with the "
            f"committed fixture (default constraints_source=fixture).",
            file=sys.stderr,
        )
        return 0

    print(f"Loading {SOURCE.name} into {WAREHOUSE}")
    con = duckdb.connect(str(WAREHOUSE))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw_constraints")
        con.execute("DROP TABLE IF EXISTS raw_constraints.area_constraints")
        con.execute(
            f"""
            CREATE TABLE raw_constraints.area_constraints AS
            SELECT * FROM read_csv_auto('{SOURCE.as_posix()}', header=true)
            """
        )
        rowcount = con.execute("SELECT count(*) FROM raw_constraints.area_constraints").fetchone()[0]
    finally:
        con.close()

    print(f"Loaded {rowcount:,} MSOA constraint rows into raw_constraints.area_constraints.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
