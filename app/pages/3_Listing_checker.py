"""Check a listing — paste a property's details, get the area + a price sanity check.

Phase 0: manual entry only. We resolve the postcode to an MSOA (postcodes.io),
show the area's scores, and compare the asking figure to the local typical. We do
not fetch or store listing-site pages.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _app_utils import (  # noqa: E402
    COMPONENTS,
    RENT_BY_BEDS,
    fmt_gbp,
    load_areas,
    price_verdict,
    resolve_postcode,
)

st.set_page_config(page_title="Check a listing", page_icon="🔎", layout="wide")
st.title("🔎 Check a listing")
st.caption(
    "Found a property (e.g. on Rightmove)? Enter its details and we'll tell you what "
    "the neighbourhood is like and whether the asking figure is reasonable for the area. "
    "Manual entry for now — we never scrape listing sites."
)

areas = load_areas()

with st.form("listing"):
    col_a, col_b = st.columns(2)
    postcode = col_a.text_input("Postcode", placeholder="e.g. SW1A 1AA")
    deal = col_b.radio("This property is", ["To rent", "To buy"], horizontal=True)
    col_c, col_d = st.columns(2)
    beds = col_c.selectbox("Bedrooms", list(RENT_BY_BEDS), index=1)
    asking = col_d.number_input(
        "Asking rent (£/month) or price (£)", min_value=0, value=0, step=50,
        help="Monthly rent for a rental, or the listed price for a sale.",
    )
    submitted = st.form_submit_button("Check this area", type="primary")

if not submitted:
    st.stop()

if not postcode.strip():
    st.warning("Enter a postcode to check.")
    st.stop()

location = resolve_postcode(postcode)
if not location or not location.get("msoa_code"):
    st.error("Couldn't find that postcode — check it and try again.")
    st.stop()
if location.get("country") not in ("England", "Wales"):
    st.warning(f"This tool covers England & Wales only (that postcode is in {location.get('country')}).")
    st.stop()

match = areas[areas["area_id"] == location["msoa_code"]]
if match.empty:
    st.info("We don't have a neighbourhood profile for that postcode yet.")
    st.stop()
row = match.iloc[0]

st.markdown(f"## {row['area_name']} · {row['region']}")
st.caption(f"Postcode {postcode.strip().upper()} → {location['msoa_name']}")

left, right = st.columns([2, 3])
with left:
    st.metric("Area score (equal weights)", f"{row['overall_score']:.0f}/100")
    st.caption(f"Confidence: {str(row['confidence_level']).title()}")
    st.info(row["why_this_area"])
with right:
    st.markdown("**How the area scores** (0–100, higher is better)")
    for col, label in COMPONENTS.items():
        value = row[col]
        if value != value:  # NaN
            st.write(f"{label}: — (no data)")
        else:
            st.progress(int(value) / 100, text=f"{label}: {int(value)}/100")

st.divider()
st.subheader("Is the asking figure reasonable?")
if asking <= 0:
    st.info("Enter an asking rent or price above to compare it to the local typical.")
elif deal == "To rent":
    local = row[RENT_BY_BEDS[beds]]
    pct, band = price_verdict(asking, local)
    if pct is None:
        st.write("No local rent benchmark for that bedroom size.")
    else:
        st.metric(
            f"Asking rent vs typical {beds.lower()} rent · {row['local_authority_name']}",
            fmt_gbp(asking), f"{pct:+.0f}% vs {fmt_gbp(local)}", delta_color="inverse",
        )
        st.write(f"This asking rent is **{band}** for a {beds.lower()} in {row['local_authority_name']} (~{fmt_gbp(local)}/month).")
else:
    local = row["median_sale_price_gbp"]
    pct, band = price_verdict(asking, local)
    if pct is None:
        st.write("No local sale-price benchmark for this area.")
    else:
        st.metric(
            f"Asking price vs median sold price · {row['area_name']}",
            fmt_gbp(asking), f"{pct:+.0f}% vs {fmt_gbp(local)}", delta_color="inverse",
        )
        st.write(f"This asking price is **{band}**. Asking prices usually sit above achieved (sold) prices, so treat a 'below' here cautiously.")

st.caption(
    "An area-level sanity check, not a property valuation — it ignores condition, exact "
    "street, floor, and bills. Rents are ONS local-authority averages by bedroom; sale "
    "prices are Land Registry MSOA medians. See **Sources & caveats** for coverage."
)
