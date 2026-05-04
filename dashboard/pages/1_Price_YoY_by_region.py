"""Price YoY by Region — deep dive on rpt_price_yoy_by_region."""

import sys
from pathlib import Path

# Ensure dashboard/ is on the path so we can import _utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st

from _utils import REGION_ORDER, fmt_gbp, fmt_pct, load_price_yoy

st.set_page_config(page_title="Price YoY by region", page_icon="📈", layout="wide")

st.title("📈 Price YoY by region")
st.markdown(
    "Median + mean sale price per region per year, with year-on-year % change. "
    "Data flows from `fct_transactions` (4.18M arm's-length sales) into "
    "`rpt_price_yoy_by_region` (10 regions × 5 years = 50 rows)."
)

yoy = load_price_yoy()

tab1, tab2, tab3 = st.tabs(["Median trajectory", "2025 YoY change", "Raw data"])

with tab1:
    st.markdown(
        "**Reading this chart:** each line is one ONS region. "
        "The slope tells you how fast the regional median is moving."
    )
    fig = px.line(
        yoy,
        x="transferred_year",
        y="median_price_gbp",
        color="region",
        category_orders={"region": REGION_ORDER},
        markers=True,
        labels={
            "transferred_year": "Year",
            "median_price_gbp": "Median sale price (GBP)",
            "region": "Region",
        },
    )
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=10, b=0))
    fig.update_yaxes(tickprefix="£", tickformat=",")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown(
        "**2025 YoY median price change.** London is the only region that fell. "
        "Wales and the North West lead at +2.4%."
    )
    yoy_2025 = yoy[yoy["transferred_year"] == 2025].sort_values(
        "median_yoy_pct", ascending=True
    )
    fig = px.bar(
        yoy_2025,
        x="median_yoy_pct",
        y="region",
        orientation="h",
        text="median_yoy_pct",
        color="median_yoy_pct",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        labels={"median_yoy_pct": "2025 YoY %", "region": "Region"},
    )
    fig.update_traces(texttemplate="%{text:+.1f}%", textposition="outside")
    fig.update_layout(height=480, margin=dict(l=0, r=0, t=10, b=0))
    fig.update_xaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    display = yoy.copy()
    display["median_price_gbp"] = display["median_price_gbp"].map(fmt_gbp)
    display["mean_price_gbp"] = display["mean_price_gbp"].map(fmt_gbp)
    display["median_yoy_pct"] = display["median_yoy_pct"].map(fmt_pct)
    display["mean_yoy_pct"] = display["mean_yoy_pct"].map(fmt_pct)
    st.dataframe(display, use_container_width=True, hide_index=True)

st.caption(
    "Source: `models/marts/analytics/rpt_price_yoy_by_region.sql` · "
    "[Lineage on dbt docs](https://rosscyking1115.github.io/uk-property-analytics/)"
)
