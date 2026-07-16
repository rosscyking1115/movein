"""Load the committed decision extract once and serve it from memory.

The API ships the small read-only data/decision.duckdb (the same extract the
Streamlit app uses). We read the 7,264 MSOA rows once and cache them; the data
is static between releases, so a new file + redeploy is the refresh mechanism.
"""

from __future__ import annotations

import datetime as dt
from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "decision.duckdb"

_QUERY = """
    select
        s.area_id, s.area_name, s.local_authority_name, s.region,
        s.affordability_score, s.safety_score, s.energy_score,
        s.flood_score, s.convenience_score,
        s.overall_score, s.overall_rank, s.available_component_count,
        s.expected_component_count, s.evidence_quality_level,
        s.all_component_source_dates_known, s.evidence_quality_notes, s.why_this_area,
        p.official_rent_monthly_gbp, p.median_sale_price_gbp,
        p.rent_source_grain, p.rent_reference_date, p.median_sale_price_confidence,
        p.rent_1bed_gbp, p.rent_2bed_gbp, p.rent_3bed_gbp, p.rent_4plus_gbp,
        p.epc_median_rating, p.crime_rate_per_1000, p.crime_record_count,
        p.crime_months_observed, p.crime_period_start, p.crime_period_end,
        p.crime_population_denominator,
        p.crime_population_reference_date, p.crime_population_geography,
        p.crime_population_source_name, p.flood_risk_flag,
        p.flood_postcode_pct, p.flood_source_status, p.flood_source_name,
        p.planning_constraint_count, p.planning_source_status,
        p.planning_source_name, p.walkable_amenity_count,
        p.nearest_station_km, p.nearest_supermarket_km, p.nearest_gp_km,
        p.nearest_school_km, p.nearest_greenspace_km,
        p.latitude, p.longitude,
        p.nearest_city, p.distance_to_city_km
    from app.rpt_neighbourhood_score as s
    left join app.rpt_area_profile_mvp as p using (area_id)
"""


def clean(record: dict) -> dict:
    """Make a pandas record JSON-safe: NaN -> None, numpy scalar -> native."""
    out: dict = {}
    for key, value in record.items():
        if value is None or pd.isna(value):
            out[key] = None
        elif hasattr(value, "item"):
            out[key] = value.item()
        else:
            out[key] = value
    return out


@lru_cache(maxsize=1)
def areas() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(_QUERY).df()
    finally:
        con.close()


@lru_cache(maxsize=1)
def _by_id() -> dict[str, dict]:
    return {rec["area_id"]: clean(rec) for rec in areas().to_dict("records")}


def get_area(msoa_code: str) -> dict | None:
    return _by_id().get(msoa_code)


def data_vintage() -> str:
    """Release date of the extract (file mtime), used for cache keys / /meta."""
    return dt.datetime.fromtimestamp(DB_PATH.stat().st_mtime, dt.timezone.utc).date().isoformat()
