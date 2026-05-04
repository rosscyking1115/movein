"""Shared utilities for the Streamlit app: read-only DuckDB connection,
cached query helpers, and a couple of formatting functions.

The `data/dashboard.duckdb` file is committed to the repo (built by
scripts/build_dashboard_db.py from the full warehouse). Streamlit Cloud
reads it directly on cold start — no live data fetch needed.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

# Path resolution: this file lives in `dashboard/`, the DB lives in `data/`,
# both directly under the repo root. Use parent.parent to land on root.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dashboard.duckdb"

# 10 ONS regions of England + Wales — used as a default sort order
REGION_ORDER = [
    "London",
    "South East",
    "East of England",
    "South West",
    "West Midlands",
    "East Midlands",
    "North West",
    "Yorkshire and the Humber",
    "Wales",
    "North East",
]


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    """Cached read-only DuckDB connection. Persists across reruns."""
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data(ttl=3600)
def load_price_yoy() -> pd.DataFrame:
    """rpt_price_yoy_by_region — 50 rows (10 regions × 5 years)."""
    return get_connection().execute(
        """
        SELECT *
        FROM analytics.rpt_price_yoy_by_region
        ORDER BY region, transferred_year
        """
    ).df()


@st.cache_data(ttl=3600)
def load_top_postcodes() -> pd.DataFrame:
    """rpt_top_postcodes_by_volume — ~500 rows."""
    return get_connection().execute(
        """
        SELECT *
        FROM analytics.rpt_top_postcodes_by_volume
        ORDER BY transferred_year, rank_within_year
        """
    ).df()


@st.cache_data(ttl=3600)
def load_new_build_premium() -> pd.DataFrame:
    """rpt_new_build_premium — 50 rows."""
    return get_connection().execute(
        """
        SELECT *
        FROM analytics.rpt_new_build_premium
        ORDER BY region, transferred_year
        """
    ).df()


def fmt_gbp(val: float | None) -> str:
    """Format a price as GBP with thousands separators, e.g. £515,000."""
    if val is None or pd.isna(val):
        return "—"
    return f"£{int(val):,}"


def fmt_pct(val: float | None) -> str:
    """Format a YoY-style percentage with sign, e.g. +2.4% or -1.0%."""
    if val is None or pd.isna(val):
        return "—"
    return f"{val:+.1f}%"
