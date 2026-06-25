"""UK Property Analytics — Streamlit dashboard home page.

Three headline KPIs at the top, three thumbnail charts below (one per
business question), and an About section linking to the live dbt docs
and the GitHub repo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _utils import (
    REGION_ORDER,
    fmt_gbp,
    fmt_pct,
    get_year_window,
    load_new_build_premium,
    load_price_yoy,
    load_top_postcodes,
)

# -------------------------------------------------------------------- page setup

st.set_page_config(
    page_title="UK Property Analytics",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

yoy = load_price_yoy()
top_pc = load_top_postcodes()
nbp = load_new_build_premium()
latest_year, prior_year = get_year_window(yoy)
first_year = int(yoy["transferred_year"].min())

st.title("🏠 UK Property Analytics")
st.markdown(
    "UK housing market study built on **HM Land Registry Price Paid** "
    f"data — every recorded property transaction in England & Wales "
    f"{first_year}–{latest_year} "
    "(≈4.99M rows, ≈157 MB Parquet). Sources → staging → intermediate → marts, "
    "tested at every layer, lineage published to GitHub Pages."
)
st.markdown(
    "📊 **[Live dbt docs (lineage + column catalogue)]"
    "(https://rosscyking1115.github.io/uk-property-analytics/)** · "
    "💻 **[GitHub repo](https://github.com/rosscyking1115/uk-property-analytics)**"
)

# -------------------------------------------------------------------- KPI row

st.markdown(f"### Headline metrics — {latest_year}")

latest_yoy = yoy[yoy["transferred_year"] == latest_year]
london_latest = latest_yoy[latest_yoy["region"] == "London"].iloc[0]

latest_sales = latest_yoy["sales_count"].sum()
if prior_year is not None:
    prior_sales = yoy[yoy["transferred_year"] == prior_year]["sales_count"].sum()
    national_volume_yoy = (latest_sales / prior_sales - 1) * 100
else:
    national_volume_yoy = None

biggest_premium = nbp[nbp["transferred_year"] == latest_year].sort_values(
    "premium_pct", ascending=False
).iloc[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label=f"London median price ({latest_year})",
        value=fmt_gbp(london_latest["median_price_gbp"]),
        delta=fmt_pct(london_latest["median_yoy_pct"]),
        help=f"Latest London median sale price and YoY movement for {latest_year}.",
    )
with col2:
    st.metric(
        label=(
            f"National sales volume ({latest_year} vs {prior_year})"
            if prior_year is not None
            else f"National sales volume ({latest_year})"
        ),
        value=f"{int(latest_sales):,}",
        delta=fmt_pct(national_volume_yoy),
        help="Total arm's-length transactions across all 10 ONS regions.",
    )
with col3:
    st.metric(
        label=f"Biggest new-build premium ({biggest_premium['region']})",
        value=fmt_pct(biggest_premium["premium_pct"]),
        help="New-build vs existing-property median price gap. Inversely correlated with regional price level.",
    )

st.markdown("---")

# -------------------------------------------------------------------- thumbnails

st.markdown("### Three business questions, three charts")

# --- Chart 1: Price YoY by region (median price over time)
st.markdown("#### 📈 Where in England & Wales has housing got more or less affordable?")
fig1 = px.line(
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
fig1.update_layout(
    height=420,
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
)
fig1.update_yaxes(tickprefix="£", tickformat=",")
st.plotly_chart(fig1, width="stretch")
st.caption(
    "Source: `rpt_price_yoy_by_region` — see "
    "[lineage](https://rosscyking1115.github.io/uk-property-analytics/#!/model/model.uk_property_analytics.rpt_price_yoy_by_region). "
    "Deep dive on the [Price YoY page](./Price_YoY_by_region)."
)

st.markdown("---")

# --- Chart 2: Top postcode areas in latest year
st.markdown(f"#### 🏘️ Which postcode areas are the hottest markets in {latest_year}?")
top_latest = top_pc[top_pc["transferred_year"] == latest_year].head(15).sort_values(
    "sales_count", ascending=True
)
fig2 = px.bar(
    top_latest,
    x="sales_count",
    y="postcode_area",
    color="region",
    orientation="h",
    category_orders={"region": REGION_ORDER},
    labels={
        "sales_count": "Number of sales",
        "postcode_area": "Postcode area",
        "region": "Region",
    },
)
fig2.update_layout(height=460, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig2, width="stretch")
st.caption(
    "Source: `rpt_top_postcodes_by_volume`. Notable: zero London postcode codes "
    f"in the {latest_year} top-15 — "
    f"{', '.join(top_latest.sort_values('sales_count', ascending=False)['postcode_area'].head(3))} "
    "lead. "
    "Deep dive on the [Top postcode areas page](./Top_postcode_areas)."
)

st.markdown("---")

# --- Chart 3: New build premium in latest year
st.markdown("#### 🏗️ How much premium do new builds command, regionally?")
nbp_latest = nbp[nbp["transferred_year"] == latest_year].sort_values(
    "premium_pct", ascending=True
)
fig3 = px.bar(
    nbp_latest,
    x="premium_pct",
    y="region",
    orientation="h",
    text="premium_pct",
    category_orders={"region": list(reversed(REGION_ORDER))},
    labels={"premium_pct": "Premium %", "region": "Region"},
)
fig3.update_traces(texttemplate="%{text:+.1f}%", textposition="outside")
fig3.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
fig3.update_xaxes(ticksuffix="%")
st.plotly_chart(fig3, width="stretch")
st.caption(
    "Source: `rpt_new_build_premium`. Inversely correlated with regional price "
    "level in the current data. Deep dive on the "
    "[New-build premium page](./New_build_premium)."
)

st.markdown("---")

# -------------------------------------------------------------------- footer

st.caption(
    "Data: HM Land Registry Price Paid (Open Government Licence v3.0). "
    "Stack: dbt-core 1.11 + DuckDB + Streamlit + GitHub Actions + GitHub Pages."
)
