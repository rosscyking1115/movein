"""Re-weighting and price-comparison logic, shared by the API endpoints.

Mirrors rpt_neighbourhood_score / the Streamlit app so the API, app, and
warehouse all agree: the overall score is a weighted mean of the components an
area has, and missing components are dropped (not scored zero).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

COMPONENTS = [
    "affordability_score",
    "safety_score",
    "energy_score",
    "flood_score",
    "convenience_score",
]
DEFAULT_WEIGHTS = {component: 1.0 for component in COMPONENTS}

# Rent column per bedroom count, for the listing price check.
RENT_BY_BEDS = {
    "1": "rent_1bed_gbp",
    "2": "rent_2bed_gbp",
    "3": "rent_3bed_gbp",
    "4plus": "rent_4plus_gbp",
    "any": "official_rent_monthly_gbp",
}


def reweight(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Add a match_score (weighted mean of available components) and sort by it."""
    w = pd.Series({c: float(weights.get(c, 0)) for c in COMPONENTS})
    scores = df[COMPONENTS]
    numerator = scores.mul(w, axis=1).sum(axis=1)
    denominator = scores.notna().mul(w, axis=1).sum(axis=1)
    out = df.copy()
    out["match_score"] = (numerator / denominator.replace(0, np.nan)).round(1)
    return out.sort_values("match_score", ascending=False, na_position="last")


def price_verdict(asking: float, local_typical: float | None) -> tuple[float | None, str]:
    """Return (% difference vs local typical, banded verdict)."""
    if local_typical is None or pd.isna(local_typical) or not local_typical:
        return None, "no local benchmark"
    pct = (asking - local_typical) / local_typical * 100
    if pct < -15:
        band = "well below the local typical"
    elif pct < -5:
        band = "below the local typical"
    elif pct <= 5:
        band = "about the local typical"
    elif pct <= 15:
        band = "above the local typical"
    else:
        band = "well above the local typical"
    return round(pct, 1), band
