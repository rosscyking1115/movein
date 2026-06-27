"""Compare 2-3 areas side by side — a trade-off receipt per column."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _app_utils import COMPONENTS, fmt_gbp, fmt_km, load_areas  # noqa: E402

st.set_page_config(page_title="Compare areas", page_icon="⚖️", layout="wide")
st.title("⚖️ Compare areas")
st.caption("Put two or three areas side by side to weigh the trade-offs directly.")

areas = load_areas()
labels = (areas["area_name"] + " — " + areas["local_authority_name"].fillna("")).tolist()
label_by_id = dict(zip(areas["area_id"], labels))

chosen = st.multiselect(
    "Choose 2–3 areas",
    options=list(areas["area_id"]),
    format_func=lambda a: label_by_id[a],
    max_selections=3,
)

if len(chosen) < 2:
    st.info("Pick at least two areas to compare.")
    st.stop()

cols = st.columns(len(chosen))
for col, area_id in zip(cols, chosen):
    row = areas[areas["area_id"] == area_id].iloc[0]
    with col:
        st.markdown(f"### {row['area_name']}")
        st.caption(f"{row['local_authority_name']} · {row['region']}")
        st.metric("Overall score (equal weights)", f"{row['overall_score']:.0f}/100")
        st.markdown("**Component scores**")
        for component, label in COMPONENTS.items():
            val = row[component]
            st.write(f"{label}: {'—' if val != val else f'{int(val)}/100'}")
        st.divider()
        st.markdown(
            f"**Typical rent:** {fmt_gbp(row['official_rent_monthly_gbp'])} /mo  \n"
            f"**Median sale price:** {fmt_gbp(row['median_sale_price_gbp'])}  \n"
            f"**EPC band:** {row['epc_median_rating'] or '—'}  \n"
            f"**Crime:** {'—' if row['crime_rate_per_1000'] != row['crime_rate_per_1000'] else f'{row['crime_rate_per_1000']:.1f} /1k/mo'}  \n"
            f"**Flood risk:** {str(row['flood_risk_flag']).title()}  \n"
            f"**Planning constraints:** {int(row['planning_constraint_count'])}  \n"
            f"**Nearest station:** {fmt_km(row['nearest_station_km'])}  \n"
            f"**Walkable essentials:** {int(row['walkable_amenity_count'])}/5  \n"
            f"**Confidence:** {str(row['confidence_level']).title()}"
        )
        st.info(row["why_this_area"])
