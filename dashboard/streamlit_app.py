"""UK Property Analytics — Streamlit dashboard home page.

Three headline KPIs at the top, three thumbnail charts below (one per
business question), and an About section linking to the live dbt docs
and the GitHub repo.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from _utils import (
    REGION_ORDER,
    fmt_gbp,
    fmt_pct,
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

st.title("🏠 UK Property Analytics")
st.markdown(
    "5-year UK housing market study built on **HM Land Registry Price Paid** "
    "data — every recorded property transaction in England & Wales 2021–2025 "
    "(≈4.99M rows, ≈157 MB Parquet). Sources → staging → intermediate → marts, "
    "tested at every layer, lineage published to GitHub Pages."
)
st.markdown(
    "📊 **[Live dbt docs (lineage + column catalogue)]"
    "(https://rosscyking1115.github.io/uk-property-analytics/)** · "
    "💻 **[GitHub repo](https://github.com/rosscyking1115/uk-property-analytics)**"
)

# -------------------------------------------------------------------- load data

yoy = load_price_yoy()
top_pc = load_top_postcodes()
nbp = load_new_build_premium()

# -------------------------------------------------------------------- KPI row

st.markdown("### Headline metrics — 2025")

london_2025 = yoy[(yoy["region"] == "London") & (yoy["transferred_year"] == 2025)].iloc[0]

national_volume_yoy = (
    yoy[yoy["transferred_year"] == 2025]["sales_count"].sum()
    / yoy[yoy["transferred_year"] == 2024]["sales_count"].sum()
    - 1
) * 100

biggest_premium = nbp[nbp["transferred_year"] == 2025].sort_values(
    "premium_pct", ascending=False
).iloc[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="London median price (2025)",
        value=fmt_gbp(london_2025["median_price_gbp"]),
        delta=fmt_pct(london_2025["median_yoy_pct"]),
        help="London is the only region with a negative YoY in 2025.",
    )
with col2:
    st.metric(
        label="National sales volume (2025 vs 2024)",
        value=f"{int(yoy[yoy['transferred_year'] == 2025]['sales_count'].sum()):,}",
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
st.plotly_chart(fig1, use_container_width=True)
st.caption(
    "Source: `rpt_price_yoy_by_region` — see "
    "[lineage](https://rosscyking1115.github.io/uk-property-analytics/#!/model/model.uk_property_analytics.rpt_price_yoy_by_region). "
    "Deep dive on the [Price YoY page](./Price_YoY_by_region)."
)

st.markdown("---")

# --- Chart 2: Top postcode areas in 2025
st.markdown("#### 🏘️ Which postcode areas are the hottest markets in 2025?")
top_2025 = top_pc[top_pc["transferred_year"] == 2025].head(15).sort_values(
    "sales_count", ascending=True
)
fig2 = px.bar(
    top_2025,
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
st.plotly_chart(fig2, use_container_width=True)
st.caption(
    "Source: `rpt_top_postcodes_by_volume`. Notable: zero London postcode codes "
    "in the 2025 top-15 — Birmingham (B), Sheffield (S), Nottingham (NG) lead. "
    "Deep dive on the [Top postcode areas page](./Top_postcode_areas)."
)

st.markdown("---")

# --- Chart 3: New build premium 2025
st.markdown("#### 🏗️ How much premium do new builds command, regionally?")
nbp_2025 = nbp[nbp["transferred_year"] == 2025].sort_values(
    "premium_pct", ascending=True
)
fig3 = px.bar(
    nbp_2025,
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
st.plotly_chart(fig3, use_container_width=True)
st.caption(
    "Source: `rpt_new_build_premium`. Inversely correlated with regional price "
    "level — North East +61.8% vs London +8.8%. Deep dive on the "
    "[New-build premium page](./New_build_premium)."
)

st.markdown("---")

# -------------------------------------------------------------------- footer

st.caption(
    "Data: HM Land Registry Price Paid (Open Government Licence v3.0). "
    "Stack: dbt-core 1.11 + DuckDB + Streamlit + GitHub Actions + GitHub Pages."
)
