"""Sources, methodology, and caveats — the honesty layer of the product."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _app_utils import load_areas  # noqa: E402

st.set_page_config(page_title="Sources & caveats", page_icon="📋", layout="wide")
st.title("📋 Sources & caveats")

areas = load_areas()
st.metric("Areas covered (England & Wales MSOAs)", f"{len(areas):,}")

st.markdown(
    """
This tool ranks **Middle layer Super Output Areas (MSOAs)** — neighbourhoods of
~7,500 residents — across England & Wales. It combines official, open data into
explainable scores. It is decision *support*, not advice, and it never labels an
area "safe" or "unsafe".

### How scoring works
Each area gets five **component scores from 0–100**, each a percentile rank
across all areas (higher is better): **affordability, safety, energy efficiency,
flood safety, convenience.** Your priority sliders set the **weights**; the match
score is the weighted average of the components an area has. Component scores are
fixed — only the weighting changes — so two people with different priorities see
different rankings from the same underlying facts.

A **missing component lowers an area's confidence** and is dropped from the
average rather than counted as zero, so absent data never looks like a bad result.

### Data sources (all Open Government / Open Database Licence)
| Signal | Source | Notes |
|---|---|---|
| Sale prices | HM Land Registry Price Paid | England & Wales; not live listings |
| Rent & affordability | ONS Price Index of Private Rents | Local-authority average rent; may be provisional |
| Geography | ONS Postcode Directory | Postcode → MSOA; 99.999% Land Registry coverage |
| Energy | Energy Performance Certificates | 23.5M certificates; some may be expired |
| Safety | Police street-level crime | 17.1M crimes; an indicator rate, never a label |
| Planning & flood | planning.data.gov.uk | Spatial overlap with constraint/flood-zone geometries |
| Convenience | OpenStreetMap | Nearest amenities + walkable-essentials count |

### Caveats worth knowing
- **Crime rate** is approximate (per a nominal MSOA population) and an *indicator*
  only — non-residential centres can read high. Never a safety verdict.
- **Affordability** uses ONS local-authority average rent, not a live listing,
  and a default income unless you set yours.
- **Convenience** uses OpenStreetMap point + building-centroid amenities; very
  rural areas may show no nearby station.
- **Door-to-door commute time** is not yet included (station proximity is).
- Figures are area-level; they describe a neighbourhood, not a specific property.
"""
)
