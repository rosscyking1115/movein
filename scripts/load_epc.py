"""Load the normalized EPC certificates into the DuckDB warehouse.

Reads `data/raw/ref_epc_normalized.csv` (produced by
`scripts/prepare_epc_seed.py`) and (re)builds `raw_epc.certificates`.
Idempotent. The committed `seeds/ref_epc_sample.csv` stays as the CI fixture;
build against the real certificates with:

    python scripts/prepare_epc_seed.py path/to/epc_bulk.zip
    python scripts/load_epc.py
    dbt build --vars 'epc_source: bulk'

If the normalized file is absent this is a no-op (exit 0), so CI and fresh
clones that only have the committed fixture are unaffected.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
NORMALIZED = ROOT / "data" / "raw" / "ref_epc_normalized.csv"
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"


def main() -> int:
    if not NORMALIZED.exists():
        print(
            f"No normalized EPC file at {NORMALIZED}.\n"
            f"Run scripts/prepare_epc_seed.py first, or build with the committed "
            f"fixture (default epc_source=fixture).",
            file=sys.stderr,
        )
        return 0

    print(f"Loading {NORMALIZED.name} into {WAREHOUSE}")
    con = duckdb.connect(str(WAREHOUSE))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw_epc")
        con.execute("DROP TABLE IF EXISTS raw_epc.certificates")
        con.execute(
            f"""
            CREATE TABLE raw_epc.certificates AS
            SELECT * FROM read_csv_auto('{NORMALIZED.as_posix()}', header=true)
            """
        )
        rowcount = con.execute("SELECT count(*) FROM raw_epc.certificates").fetchone()[0]
    finally:
        con.close()

    print(f"Loaded {rowcount:,} EPC certificates into raw_epc.certificates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
