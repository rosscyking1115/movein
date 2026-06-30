"""Add MSOA population-weighted centroid lat/lng to data/decision.duckdb.

The extract ships the area facts but no coordinates; the website map needs them.
This joins seeds/ref_msoa_centroid.csv (ONS MSOA Dec-2021 population-weighted
centroids, WGS84) into app.rpt_area_profile_mvp in place, so the API can serve a
latitude/longitude per area without a full warehouse rebuild. The dbt model
rpt_area_profile_mvp.sql joins the same seed for full rebuilds — keep in sync.

Usage: python scripts/add_centroids.py [--db PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "decision.duckdb"
SEED = ROOT / "seeds" / "ref_msoa_centroid.csv"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    args = ap.parse_args()

    if not SEED.exists():
        print(f"Seed not found: {SEED}", file=sys.stderr)
        return 1

    con = duckdb.connect(args.db)
    cols = {r[0] for r in con.execute("describe app.rpt_area_profile_mvp").fetchall()}
    keep = [c for c in cols if c not in ("latitude", "longitude")]
    select_cols = ", ".join(f"p.{c}" for c in keep)

    con.execute(f"create temp table cen as select * from read_csv_auto('{SEED.as_posix()}', header=true)")
    con.execute(
        f"""
        create or replace table app.rpt_area_profile_mvp as
        select {select_cols}, cen.latitude, cen.longitude
        from app.rpt_area_profile_mvp as p
        left join cen on p.area_id = cen.area_id
        """
    )
    n, miss = con.execute(
        "select count(*), count(*) filter (where latitude is null) from app.rpt_area_profile_mvp"
    ).fetchone()
    con.close()
    print(f"Added centroids to {n:,} areas ({miss} without coordinates).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
