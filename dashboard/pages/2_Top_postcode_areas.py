"""Top postcode areas by volume — deep dive on rpt_top_postcodes_by_volume."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st

from _utils import REGION_ORDER, fmt_gbp, load_top_postcodes

st.set_page_config(page_title="Top postcode areas", page_icon="🏘️", layout="wide")

st.title("🏘️ Top postcode areas by volume")
st.markdown(
    "Postcode-area leaderboard by transaction count per year. "
    "Each row is one postcode area (the leading 1–2 letters of a UK postcode, "
    "e.g. `B` for Birmingham, `SW` for South-West London)."
)

top_pc = load_top_postcodes()

# Year + top-N selectors
years = sorted(top_pc["transferred_year"].unique(), reverse=True)
col_y, col_n = st.columns([1, 1])
with col_y:
    selected_year = st.selectbox("Year", years, index=0)
with col_n:
    top_n = st.slider("Show top N", min_value=5, max_value=30, value=15, step=5)

# Filter + sort
year_data = top_pc[top_pc["transferred_year"] == selected_year]
top_n_data = year_data.head(top_n).sort_values("sales_count", ascending=True)

st.markdown(f"### Top {top_n} postcode areas in {selected_year}")
fig = px.bar(
    top_n_data,
    x="sales_count",
    y="postcode_area",
    color="region",
    orientation="h",
    category_orders={"region": REGION_ORDER},
    text="sales_count",
    labels={
        "sales_count": "Number of sales",
        "postcode_area": "Postcode area",
        "region": "Region",
    },
    hover_data={"median_price_gbp": ":,"},
)
fig.update_traces(texttemplate="%{text:,}", textposition="outside")
fig.update_layout(height=560, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Same data with median sale price")
display = top_n_data.sort_values("rank_within_year").copy()
display["median_price_gbp"] = display["median_price_gbp"].map(fmt_gbp)
display = display[
    ["rank_within_year", "postcode_area", "region", "sales_count", "median_price_gbp"]
]
display.columns = ["Rank", "Area", "Region", "Sales count", "Median price"]
st.dataframe(display, use_container_width=True, hide_index=True)

st.caption(
    "Source: `models/marts/analytics/rpt_top_postcodes_by_volume.sql` · "
    "Note: London postcode codes (`E`, `EC`, `N`, `NW`, `SE`, `SW`, `W`, `WC`) "
    "split the city across 8+ areas, so single-letter codes covering whole cities "
    "(Birmingham `B`, Sheffield `S`) often outrank them individually."
)
