"""Add nearest city-centre + distance to data/decision.duckdb.

Uses each area's population-weighted centroid (added by add_centroids.py) and the
major-city seed (seeds/ref_city_centre.csv) to find the nearest city centre and
the great-circle distance to it, so an area page can say "3.2 km from Manchester
centre". Recomputed in place (no full rebuild); the dbt model rpt_area_profile_mvp
computes the same thing for full rebuilds — keep in sync.

Usage: python scripts/add_city_distance.py [--db PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "decision.duckdb"
SEED = ROOT / "seeds" / "ref_city_centre.csv"

# Great-circle (haversine) km between an area and a city, then arg-min per area.
NEAREST_SQL = """
with a as (
    select area_id, latitude, longitude
    from app.rpt_area_profile_mvp
    where latitude is not null and longitude is not null
),
d as (
    select
        a.area_id,
        c.city,
        6371 * 2 * asin(sqrt(
            pow(sin(radians((c.latitude - a.latitude) / 2)), 2)
            + cos(radians(a.latitude)) * cos(radians(c.latitude))
            * pow(sin(radians((c.longitude - a.longitude) / 2)), 2)
        )) as km,
        row_number() over (
            partition by a.area_id order by 6371 * 2 * asin(sqrt(
                pow(sin(radians((c.latitude - a.latitude) / 2)), 2)
                + cos(radians(a.latitude)) * cos(radians(c.latitude))
                * pow(sin(radians((c.longitude - a.longitude) / 2)), 2)
            )) asc
        ) as rn
    from a
    cross join cty as c
)
select area_id, city as nearest_city, round(km, 1) as distance_to_city_km
from d where rn = 1
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    args = ap.parse_args()
    if not SEED.exists():
        print(f"Seed not found: {SEED}", file=sys.stderr)
        return 1

    con = duckdb.connect(args.db)
    con.execute(f"create temp table cty as select * from read_csv_auto('{SEED.as_posix()}', header=true)")
    con.execute(f"create temp table near as {NEAREST_SQL}")

    cols = {r[0] for r in con.execute("describe app.rpt_area_profile_mvp").fetchall()}
    keep = [c for c in cols if c not in ("nearest_city", "distance_to_city_km")]
    select_cols = ", ".join(f"p.{c}" for c in keep)
    con.execute(
        f"""
        create or replace table app.rpt_area_profile_mvp as
        select {select_cols}, near.nearest_city, near.distance_to_city_km
        from app.rpt_area_profile_mvp as p
        left join near using (area_id)
        """
    )
    n, miss = con.execute(
        "select count(*), count(*) filter (where nearest_city is null) from app.rpt_area_profile_mvp"
    ).fetchone()
    con.close()
    print(f"Added city distance to {n:,} areas ({miss} without).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
