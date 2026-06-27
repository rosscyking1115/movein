"""Roll OpenStreetMap amenities up to per-MSOA convenience metrics.

Reads a Geofabrik .osm.pbf extract with DuckDB spatial (ST_ReadOSM), classifies
amenity nodes (supermarket, school, GP/health, pharmacy, green space, station),
and for each MSOA centroid (derived from the loaded ONSPD postcodes) computes
the nearest-amenity distance per type and a walkable-essentials count. Output:

  data/raw/ref_amenity_access.csv
    area_id, nearest_station_km, nearest_supermarket_km, nearest_gp_km,
    nearest_school_km, nearest_greenspace_km, walkable_amenity_count

Distances use ST_Distance_Sphere (metres). Only node POIs are used (way/polygon
amenities are not resolved) — a documented MVP approximation. Requires the
geography to be loaded first (scripts/load_geography.py).

Usage:
    python scripts/prepare_amenity_access.py path/to/great-britain-latest.osm.pbf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "raw" / "ref_amenity_access.csv"
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"
# ~0.16 degrees latitude is roughly an 18 km candidate cap for the nearest search.
CANDIDATE_DEGREES = 0.16


def prepare(pbf_path: Path, output_path: Path, walkable_radius_km: float) -> int:
    if not WAREHOUSE.exists():
        raise ValueError(f"Warehouse not found at {WAREHOUSE}; run load_geography.py first.")
    walk_m = walkable_radius_km * 1000.0

    con = duckdb.connect(str(WAREHOUSE))
    con.execute("INSTALL spatial; LOAD spatial;")
    # Bound memory and allow spilling — the GB OSM extract is large.
    con.execute("SET memory_limit='6GB'")
    con.execute(f"SET temp_directory='{(ROOT / 'data' / 'duckdb_tmp').as_posix()}'")
    if not con.execute("SELECT count(*) FROM information_schema.tables "
                       "WHERE table_schema='raw_geo' AND table_name='onspd_postcodes'").fetchone()[0]:
        raise ValueError("raw_geo.onspd_postcodes is missing; run load_geography.py first.")

    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE centroids AS
        SELECT area_id, ST_Point(avg(longitude), avg(latitude)) AS pt
        FROM raw_geo.onspd_postcodes
        WHERE (area_id LIKE 'E02%' OR area_id LIKE 'W02%')
          AND latitude IS NOT NULL AND longitude IS NOT NULL
        GROUP BY area_id
        """
    )

    pbf = pbf_path.as_posix()
    classify = """
        CASE
            WHEN tags['shop'] = 'supermarket' THEN 'supermarket'
            WHEN tags['amenity'] = 'school' THEN 'school'
            WHEN tags['amenity'] IN ('doctors', 'clinic', 'hospital')
                 OR tags['healthcare'] IS NOT NULL THEN 'gp'
            WHEN tags['amenity'] = 'pharmacy' THEN 'pharmacy'
            WHEN tags['leisure'] IN ('park', 'garden', 'nature_reserve') THEN 'greenspace'
            WHEN tags['railway'] IN ('station', 'halt')
                 OR tags['station'] IS NOT NULL THEN 'station'
        END
    """
    relevant = """
        tags['shop'] = 'supermarket'
        OR tags['amenity'] IN ('school', 'doctors', 'clinic', 'hospital', 'pharmacy')
        OR tags['healthcare'] IS NOT NULL
        OR tags['leisure'] IN ('park', 'garden', 'nature_reserve')
        OR tags['railway'] IN ('station', 'halt')
        OR tags['station'] IS NOT NULL
    """

    # Many amenities (schools, supermarkets, parks) are mapped as ways/polygons,
    # not nodes, so node-only extraction badly undercounts. Resolve way centroids
    # from member-node coordinates. To stay in bounded memory, materialise only
    # the nodes referenced by tagged ways rather than all ~100M GB nodes.
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE way_tags AS
        SELECT id, refs, {classify} AS amenity_type
        FROM ST_ReadOSM('{pbf}')
        WHERE kind = 'way' AND ({relevant})
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE way_refs AS
        SELECT id, amenity_type, unnest(refs) AS node_id
        FROM way_tags WHERE amenity_type IS NOT NULL
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE osm_nodes AS
        SELECT id, lat, lon FROM ST_ReadOSM('{pbf}')
        WHERE kind = 'node' AND lat IS NOT NULL
          AND id IN (SELECT node_id FROM way_refs)
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE node_poi AS
        SELECT {classify} AS amenity_type, ST_Point(lon, lat) AS pt
        FROM ST_ReadOSM('{pbf}')
        WHERE kind = 'node' AND lat IS NOT NULL AND lon IS NOT NULL AND ({relevant})
        """
    )

    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE way_poi AS
        SELECT r.amenity_type, ST_Point(avg(n.lon), avg(n.lat)) AS pt
        FROM way_refs AS r JOIN osm_nodes AS n ON r.node_id = n.id
        GROUP BY r.id, r.amenity_type
        """
    )

    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE poi AS
        SELECT amenity_type, pt FROM node_poi WHERE amenity_type IS NOT NULL
        UNION ALL
        SELECT amenity_type, pt FROM way_poi
        """
    )
    print(f"  classified {con.execute('SELECT count(*) FROM poi').fetchone()[0]:,} amenity points "
          f"(nodes + way centroids)", file=sys.stderr)

    con.execute(
        f"""
        COPY (
            WITH pairs AS (
                SELECT
                    c.area_id,
                    p.amenity_type,
                    ST_Distance_Sphere(c.pt, p.pt) AS dist_m
                FROM centroids AS c
                JOIN poi AS p
                    ON ST_DWithin(c.pt, p.pt, {CANDIDATE_DEGREES})
            )
            SELECT
                c.area_id,
                round(min(CASE WHEN p.amenity_type = 'station' THEN p.dist_m END) / 1000, 2) AS nearest_station_km,
                round(min(CASE WHEN p.amenity_type = 'supermarket' THEN p.dist_m END) / 1000, 2) AS nearest_supermarket_km,
                round(min(CASE WHEN p.amenity_type = 'gp' THEN p.dist_m END) / 1000, 2) AS nearest_gp_km,
                round(min(CASE WHEN p.amenity_type = 'school' THEN p.dist_m END) / 1000, 2) AS nearest_school_km,
                round(min(CASE WHEN p.amenity_type = 'greenspace' THEN p.dist_m END) / 1000, 2) AS nearest_greenspace_km,
                count(DISTINCT CASE
                    WHEN p.dist_m <= {walk_m}
                         AND p.amenity_type IN ('supermarket', 'gp', 'school', 'pharmacy', 'greenspace')
                    THEN p.amenity_type
                END) AS walkable_amenity_count
            FROM centroids AS c
            LEFT JOIN pairs AS p ON c.area_id = p.area_id
            GROUP BY c.area_id
            ORDER BY c.area_id
        ) TO '{output_path.as_posix()}' (HEADER, DELIMITER ',')
        """
    )
    rows = con.execute("SELECT count(*) FROM centroids").fetchone()[0]
    con.close()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pbf_path", type=Path, help="Path to a Geofabrik .osm.pbf extract")
    parser.add_argument("--walkable-radius-km", type=float, default=1.0)
    args = parser.parse_args()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        rows = prepare(args.pbf_path, OUTPUT, args.walkable_radius_km)
    except (OSError, ValueError, duckdb.Error) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(f"[done] wrote {rows:,} MSOA amenity-access rows to {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
