"""Renter decision app — 'Where to live' shortlist for England & Wales.

The user sets income, budget, and how much each factor matters; the app ranks
MSOAs by a personalised match score that updates live, and explains every area.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _app_utils import (  # noqa: E402
    COMPONENTS,
    REGIONS,
    fmt_gbp,
    fmt_km,
    load_areas,
    reweight,
)

st.set_page_config(page_title="Where to live — UK", page_icon="🏘️", layout="wide")

st.title("🏘️ Where to live")
st.caption(
    "An explainable neighbourhood shortlist for England & Wales renters and movers. "
    "Set your budget and what matters to you — the ranking updates live, and every "
    "area explains itself. Indicators only, never a 'safe/unsafe' label."
)

areas = load_areas()

with st.sidebar:
    st.header("Your situation")
    income = st.number_input(
        "Net monthly income (£)", min_value=500, max_value=20000, value=2500, step=100,
        help="Used to show rent as a share of your income.",
    )
    max_rent = st.number_input(
        "Maximum monthly rent (£)", min_value=300, max_value=6000, value=1500, step=50,
        help="Areas whose typical rent is above this are filtered out.",
    )
    chosen_regions = st.multiselect("Regions (optional)", REGIONS, default=[])

    st.header("Your priorities")
    st.caption("How much each factor matters (0 = ignore it).")
    weights = {
        col: st.slider(label, min_value=0, max_value=5, value=3)
        for col, label in COMPONENTS.items()
    }

if sum(weights.values()) == 0:
    st.warning("Set at least one priority above 0 to rank areas.")
    st.stop()

# Budget + region filter, then live re-rank from the stored component scores.
shortlist = areas.copy()
shortlist = shortlist[
    shortlist["official_rent_monthly_gbp"].isna()
    | (shortlist["official_rent_monthly_gbp"] <= max_rent)
]
if chosen_regions:
    shortlist = shortlist[shortlist["region"].isin(chosen_regions)]
shortlist = reweight(shortlist, weights)
shortlist["rent_pct_income"] = shortlist["official_rent_monthly_gbp"] / income * 100

st.subheader(f"{len(shortlist):,} areas within budget — top matches")

if shortlist.empty:
    st.info("No areas match. Try raising your maximum rent or widening the regions.")
    st.stop()

table = shortlist.head(25)[[
    "area_name", "region", "match_score", "official_rent_monthly_gbp",
    "rent_pct_income", "epc_median_rating", "crime_rate_per_1000",
    "flood_risk_flag", "walkable_amenity_count",
]].rename(columns={
    "area_name": "Area",
    "region": "Region",
    "match_score": "Match",
    "official_rent_monthly_gbp": "Rent /mo",
    "rent_pct_income": "Rent % income",
    "epc_median_rating": "EPC",
    "crime_rate_per_1000": "Crime /1k",
    "flood_risk_flag": "Flood",
    "walkable_amenity_count": "Walkable",
})

st.dataframe(
    table,
    hide_index=True,
    width="stretch",
    column_config={
        "Match": st.column_config.ProgressColumn(
            "Match", min_value=0, max_value=100, format="%d"
        ),
        "Rent /mo": st.column_config.NumberColumn("Rent /mo", format="£%d"),
        "Rent % income": st.column_config.NumberColumn("Rent % income", format="%.0f%%"),
        "Crime /1k": st.column_config.NumberColumn("Crime /1k", format="%.1f"),
        "Walkable": st.column_config.NumberColumn("Walkable", format="%d/5"),
    },
)
st.caption(
    "Match score is the weighted average of each area's 0–100 component scores, "
    "using your priority sliders. Component scores are fixed percentile ranks "
    "across all areas; only the weighting changes."
)

# ----------------------------------------------------------- trade-off receipt
st.divider()
st.subheader("Trade-off receipt")
labels = shortlist["area_name"] + " — " + shortlist["local_authority_name"].fillna("")
choice = st.selectbox("Inspect an area", options=list(shortlist["area_id"]),
                      format_func=lambda a: labels[shortlist["area_id"] == a].iloc[0])
row = shortlist[shortlist["area_id"] == choice].iloc[0]

st.markdown(f"### {row['area_name']}  ·  {row['region']}")
top = st.columns(4)
top[0].metric("Match score", f"{row['match_score']:.0f}/100")
top[1].metric("Typical rent", fmt_gbp(row["official_rent_monthly_gbp"]),
              f"{row['rent_pct_income']:.0f}% of income" if row["rent_pct_income"] == row["rent_pct_income"] else None)
top[2].metric("Median sale price", fmt_gbp(row["median_sale_price_gbp"]))
top[3].metric("Confidence", str(row["confidence_level"]).title())

st.markdown("**How it scores** (0–100, higher is better)")
for col, label in COMPONENTS.items():
    val = row[col]
    if val != val:  # NaN
        st.write(f"{label}: — (no data)")
    else:
        st.progress(int(val) / 100, text=f"{label}: {int(val)}/100")

facts = st.columns(3)
facts[0].markdown(
    f"**Energy (EPC):** {row['epc_median_rating'] or '—'}  \n"
    f"**Crime:** {row['crime_rate_per_1000']:.1f} /1,000/mo"
    if row["crime_rate_per_1000"] == row["crime_rate_per_1000"] else "**Crime:** —"
)
facts[1].markdown(
    f"**Flood risk:** {str(row['flood_risk_flag']).title()}  \n"
    f"**Planning constraints:** {int(row['planning_constraint_count'])}"
)
facts[2].markdown(
    f"**Nearest station:** {fmt_km(row['nearest_station_km'])}  \n"
    f"**Nearest school / GP:** {fmt_km(row['nearest_school_km'])} / {fmt_km(row['nearest_gp_km'])}  \n"
    f"**Walkable essentials:** {int(row['walkable_amenity_count'])}/5"
)

st.info(row["why_this_area"])
st.caption(
    "Rents are ONS local-authority averages; crime and flood are measured "
    "indicators, not labels. See **Sources & caveats** for coverage and freshness."
)
