"""Print reproducible coverage statistics from the shipped decision extract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb


def _rows(connection: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, object]]:
    result = connection.execute(sql)
    columns = [item[0] for item in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("extract", type=Path, nargs="?", default=Path("data/decision.duckdb"))
    args = parser.parse_args()

    with duckdb.connect(str(args.extract), read_only=True) as connection:
        summary = {
            "area_rows": connection.execute(
                "select count(*) from app.rpt_neighbourhood_score"
            ).fetchone()[0],
            "countries": _rows(
                connection,
                """
                select
                    case left(area_id, 1) when 'E' then 'England' when 'W' then 'Wales' end as country,
                    count(*) as areas
                from app.rpt_neighbourhood_score
                group by 1
                order by country
                """,
            ),
            "evidence_quality": _rows(
                connection,
                """
                select evidence_quality_level, count(*) as areas
                from app.rpt_neighbourhood_score
                group by evidence_quality_level
                order by evidence_quality_level
                """,
            ),
            "component_coverage": _rows(
                connection,
                """
                select
                    count(affordability_score) as affordability,
                    count(safety_score) as safety,
                    count(energy_score) as energy,
                    count(flood_score) as flood,
                    count(convenience_score) as convenience,
                    count(overall_score) as overall
                from app.rpt_neighbourhood_score
                """,
            )[0],
            "crime_denominator": _rows(
                connection,
                """
                select
                    count(crime_population_denominator) as covered_areas,
                    min(crime_population_reference_date) as earliest_reference_date,
                    max(crime_population_reference_date) as latest_reference_date,
                    min(crime_population_geography) as geography,
                    min(crime_population_source_name) as source_name
                from app.rpt_area_profile_mvp
                """,
            )[0],
            "constraint_coverage": _rows(
                connection,
                """
                select
                    case left(s.area_id, 1)
                        when 'E' then 'England'
                        when 'W' then 'Wales'
                    end as country,
                    p.planning_source_status,
                    p.flood_source_status,
                    count(*) as areas
                from app.rpt_neighbourhood_score as s
                join app.rpt_area_profile_mvp as p using (area_id)
                group by all
                order by country, p.planning_source_status, p.flood_source_status
                """,
            ),
        }

    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
