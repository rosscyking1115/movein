"""Shared helpers for the renter decision app.

Reads the committed slim extract data/decision.duckdb (built by
scripts/build_decision_db.py from the warehouse). The app never re-runs the
pipeline — it loads the per-area scores + facts once and re-weights them in
memory as the user moves the priority sliders.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "decision.duckdb"

# Component score column -> friendly label. These are the 0-100 stored facts;
# the user only changes how they are *combined*, never the scores themselves.
COMPONENTS: dict[str, str] = {
    "affordability_score": "Affordability",
    "safety_score": "Safety",
    "energy_score": "Energy efficiency",
    "flood_score": "Flood safety",
    "convenience_score": "Convenience",
}

REGIONS = [
    "London", "South East", "East of England", "South West", "West Midlands",
    "East Midlands", "North West", "Yorkshire and The Humber", "Wales", "North East",
]


@st.cache_resource
def _connect() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data(ttl=3600)
def load_areas() -> pd.DataFrame:
    """One row per MSOA: component + overall scores joined to the raw facts."""
    return _connect().execute(
        """
        select
            s.area_id, s.area_name, s.local_authority_name, s.region,
            s.affordability_score, s.safety_score, s.energy_score,
            s.flood_score, s.convenience_score,
            s.overall_score, s.confidence_level, s.components_available,
            s.why_this_area,
            p.official_rent_monthly_gbp, p.median_sale_price_gbp,
            p.epc_median_rating, p.crime_rate_per_1000, p.flood_risk_flag,
            p.planning_constraint_count, p.walkable_amenity_count,
            p.nearest_station_km, p.nearest_supermarket_km, p.nearest_gp_km,
            p.nearest_school_km, p.nearest_greenspace_km
        from app.rpt_neighbourhood_score as s
        left join app.rpt_area_profile_mvp as p using (area_id)
        """
    ).df()


def reweight(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Recompute a personalised match score from the stored component scores.

    match = weighted mean of the components an area has (missing components are
    dropped, not scored zero), exactly mirroring rpt_neighbourhood_score so the
    app and warehouse agree on equal weights.
    """
    cols = list(COMPONENTS)
    w = pd.Series({c: float(weights.get(c, 0)) for c in cols})
    scores = df[cols]
    numerator = scores.mul(w, axis=1).sum(axis=1)
    denominator = scores.notna().mul(w, axis=1).sum(axis=1)
    out = df.copy()
    out["match_score"] = (numerator / denominator.replace(0, np.nan)).round(1)
    return out.sort_values("match_score", ascending=False, na_position="last")


def fmt_gbp(val: float | None) -> str:
    if val is None or pd.isna(val):
        return "—"
    return f"£{int(val):,}"


def fmt_km(val: float | None) -> str:
    if val is None or pd.isna(val):
        return "—"
    return f"{val:.1f} km"


def fmt_score(val: float | None) -> str:
    if val is None or pd.isna(val):
        return "—"
    return f"{val:.0f}/100"
