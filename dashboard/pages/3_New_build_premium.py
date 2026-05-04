"""New-build premium — deep dive on rpt_new_build_premium."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st

from _utils import REGION_ORDER, fmt_gbp, fmt_pct, load_new_build_premium

st.set_page_config(page_title="New-build premium", page_icon="🏗️", layout="wide")

st.title("🏗️ New-build premium by region")
st.markdown(
    "Median-price premium that new builds command over existing properties, "
    "by region and year. Computed as "
    "`100 × (new_build_median - existing_median) / existing_median`. "
    "Excludes 'Unknown' region."
)

nbp = load_new_build_premium()

tab1, tab2, tab3 = st.tabs(["2025 snapshot", "Premium over time", "Raw data"])

with tab1:
    st.markdown(
        "**2025 by region.** Inversely correlated with regional price level — "
        "the cheapest regions have the largest new-build premiums (scarcity), "
        "while saturated London has the smallest."
    )
    nbp_2025 = nbp[nbp["transferred_year"] == 2025].sort_values(
        "premium_pct", ascending=True
    )
    fig = px.bar(
        nbp_2025,
        x="premium_pct",
        y="region",
        orientation="h",
        text="premium_pct",
        color="premium_pct",
        color_continuous_scale="Blues",
        labels={"premium_pct": "Premium %", "region": "Region"},
    )
    fig.update_traces(texttemplate="%{text:+.1f}%", textposition="outside")
    fig.update_layout(height=480, margin=dict(l=0, r=0, t=10, b=0))
    fig.update_xaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown(
        "**Premium % over time per region.** Mostly stable — the regional "
        "ordering doesn't shuffle much year-to-year."
    )
    fig = px.line(
        nbp,
        x="transferred_year",
        y="premium_pct",
        color="region",
        category_orders={"region": REGION_ORDER},
        markers=True,
        labels={
            "transferred_year": "Year",
            "premium_pct": "Premium %",
            "region": "Region",
        },
    )
    fig.update_layout(height=520, margin=dict(l=0, r=0, t=10, b=0))
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    display = nbp.copy()
    display["new_build_median_price_gbp"] = display["new_build_median_price_gbp"].map(fmt_gbp)
    display["existing_median_price_gbp"] = display["existing_median_price_gbp"].map(fmt_gbp)
    display["premium_pct"] = display["premium_pct"].map(fmt_pct)
    show = display[
        [
            "region",
            "transferred_year",
            "new_build_count",
            "existing_count",
            "new_build_median_price_gbp",
            "existing_median_price_gbp",
            "premium_pct",
        ]
    ]
    st.dataframe(show, use_container_width=True, hide_index=True)

st.caption(
    "Source: `models/marts/analytics/rpt_new_build_premium.sql` · "
    "[Lineage on dbt docs](https://rosscyking1115.github.io/uk-property-analytics/)"
)
