"""Roll planning constraints and flood-risk zones up to MSOA via spatial join.

Reads planning.data.gov.uk constraint CSVs (WKT geometry, directly downloadable,
no login) and the loaded raw_geo.onspd_postcodes centroids, and uses DuckDB
spatial point-in-polygon to attribute each constraint to the MSOAs whose
postcodes fall inside it. Outputs the small per-MSOA seed:

  data/raw/ref_area_constraints.csv
    area_id, planning_constraint_count, flood_risk_flag, flood_postcode_pct

planning_constraint_count = distinct planning constraint entities (conservation
areas, green belt, Article 4 areas, tree preservation zones) touching the MSOA.
flood_risk_flag (low/medium/high) is banded from the share of the MSOA's
postcodes that fall inside an Environment Agency flood-risk zone.

Every constraint CSV in the input directory is treated as a planning constraint
except flood-risk-zone.csv, which drives the flood flag. Requires the geography
to be loaded first (scripts/load_geography.py).

Usage:
    python scripts/prepare_area_constraints.py path/to/planning_csv_dir
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "raw" / "ref_area_constraints.csv"
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"
FLOOD_STEM = "flood-risk-zone"
FLOOD_MEDIUM_PCT = 5.0
FLOOD_HIGH_PCT = 20.0


def _load_geometries(con: duckdb.DuckDBPyConnection, table: str, csv_path: Path) -> int:
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE {table} AS
        SELECT reference, ST_GeomFromText(geometry) AS geom
        FROM read_csv_auto('{csv_path.as_posix()}', header=true, ignore_errors=true,
                           types={{'geometry': 'VARCHAR'}})
        WHERE geometry IS NOT NULL AND length(geometry) > 0
        """
    )
    return con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def prepare(csv_dir: Path, output_path: Path) -> int:
    if not WAREHOUSE.exists():
        raise ValueError(f"Warehouse not found at {WAREHOUSE}; run load_geography.py first.")

    con = duckdb.connect(str(WAREHOUSE))
    con.execute("INSTALL spatial; LOAD spatial;")
    if not con.execute("SELECT count(*) FROM information_schema.tables "
                       "WHERE table_schema='raw_geo' AND table_name='onspd_postcodes'").fetchone()[0]:
        raise ValueError("raw_geo.onspd_postcodes is missing; run load_geography.py first.")

    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE pc AS
        SELECT postcode, area_id, ST_Point(longitude, latitude) AS pt
        FROM raw_geo.onspd_postcodes
        WHERE area_id IS NOT NULL AND latitude IS NOT NULL AND longitude IS NOT NULL
        """
    )
    con.execute("CREATE OR REPLACE TEMP TABLE planning_hits (area_id VARCHAR, dataset VARCHAR, reference VARCHAR)")

    csv_paths = sorted(csv_dir.glob("*.csv"))
    if not csv_paths:
        raise ValueError(f"No constraint CSVs found in {csv_dir}")

    flood_path: Path | None = None
    for csv_path in csv_paths:
        dataset = csv_path.stem
        if dataset == FLOOD_STEM:
            flood_path = csv_path
            continue
        count = _load_geometries(con, "constraint_geom", csv_path)
        con.execute(
            f"""
            INSERT INTO planning_hits
            SELECT DISTINCT pc.area_id, '{dataset}' AS dataset, c.reference
            FROM pc JOIN constraint_geom AS c ON ST_Contains(c.geom, pc.pt)
            """
        )
        print(f"  {dataset}: {count:,} polygons joined", file=sys.stderr)

    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE area_base AS
        SELECT area_id, count(*) AS total_postcodes
        FROM pc GROUP BY area_id
        """
    )

    if flood_path is not None:
        _load_geometries(con, "flood_geom", flood_path)
        con.execute(
            """
            CREATE OR REPLACE TEMP TABLE flood_hits AS
            SELECT pc.area_id, count(DISTINCT pc.postcode) AS flood_postcodes
            FROM pc JOIN flood_geom AS f ON ST_Contains(f.geom, pc.pt)
            GROUP BY pc.area_id
            """
        )
        print("  flood-risk-zone joined", file=sys.stderr)
    else:
        con.execute("CREATE OR REPLACE TEMP TABLE flood_hits AS SELECT NULL::VARCHAR AS area_id, 0 AS flood_postcodes WHERE false")

    con.execute(
        f"""
        COPY (
            SELECT
                b.area_id,
                coalesce(p.constraint_count, 0) AS planning_constraint_count,
                round(100.0 * coalesce(f.flood_postcodes, 0) / b.total_postcodes, 1) AS flood_postcode_pct,
                CASE
                    WHEN 100.0 * coalesce(f.flood_postcodes, 0) / b.total_postcodes >= {FLOOD_HIGH_PCT} THEN 'high'
                    WHEN 100.0 * coalesce(f.flood_postcodes, 0) / b.total_postcodes >= {FLOOD_MEDIUM_PCT} THEN 'medium'
                    ELSE 'low'
                END AS flood_risk_flag
            FROM area_base AS b
            LEFT JOIN (
                SELECT area_id, count(*) AS constraint_count FROM planning_hits GROUP BY area_id
            ) AS p ON b.area_id = p.area_id
            LEFT JOIN flood_hits AS f ON b.area_id = f.area_id
            ORDER BY b.area_id
        ) TO '{output_path.as_posix()}' (HEADER, DELIMITER ',')
        """
    )
    rows = con.execute("SELECT count(*) FROM area_base").fetchone()[0]
    con.close()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_dir", type=Path, help="Directory of planning.data.gov.uk constraint CSVs")
    args = parser.parse_args()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        rows = prepare(args.csv_dir, OUTPUT)
    except (OSError, ValueError, duckdb.Error) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(f"[done] wrote {rows:,} MSOA constraint rows to {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
