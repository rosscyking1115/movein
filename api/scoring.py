"""Re-weighting and price-comparison logic shared by the API endpoints.

Mirrors rpt_neighbourhood_score so the API, web app, and warehouse agree: the
overall score is a weighted geometric mean of the components an area has, and
missing components are dropped rather than scored as zero.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

_CONTRACT_PATH = Path(__file__).resolve().parent.parent / "contracts" / "neighbourhood-scoring-v2.json"
_CONTRACT = json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))
CONTRACT_VERSION = _CONTRACT["schema_version"]
COMPONENTS = list(_CONTRACT["components"])
DEFAULT_WEIGHTS = {
    component: float(config["default_weight"])
    for component, config in _CONTRACT["components"].items()
}
COMPONENT_FLOOR = float(_CONTRACT["component_floor"])
ROUNDING_DECIMAL_PLACES = int(_CONTRACT["rounding_decimal_places"])
TIE_ORDER = _CONTRACT["tie_order"]
MIN_WEIGHT = float(_CONTRACT["allowed_weight"]["minimum"])
MAX_WEIGHT = float(_CONTRACT["allowed_weight"]["maximum"])

# Rent column per bedroom count, for the listing price check.
RENT_BY_BEDS = {
    "1": "rent_1bed_gbp",
    "2": "rent_2bed_gbp",
    "3": "rent_3bed_gbp",
    "4plus": "rent_4plus_gbp",
    "any": "official_rent_monthly_gbp",
}


def reweight(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Add a match_score (weighted GEOMETRIC mean of available components) and sort.

    Mirrors the warehouse overall_score: a geometric mean (components floored at 1)
    so one excellent pillar can't mask a poor one. Missing components are dropped.
    """
    effective_weights = DEFAULT_WEIGHTS if not weights else weights
    parsed_weights = {c: float(effective_weights.get(c, 0)) for c in COMPONENTS}
    if any(not np.isfinite(value) or not MIN_WEIGHT <= value <= MAX_WEIGHT for value in parsed_weights.values()):
        raise ValueError(f"Weights must be finite numbers from {MIN_WEIGHT:g} to {MAX_WEIGHT:g}.")
    w = pd.Series(parsed_weights)
    scores = df[COMPONENTS].apply(pd.to_numeric, errors="coerce").replace(
        [np.inf, -np.inf], np.nan
    )
    log_scores = np.log(scores.clip(lower=COMPONENT_FLOOR))
    numerator = log_scores.mul(w, axis=1).sum(axis=1)
    denominator = scores.notna().mul(w, axis=1).sum(axis=1)
    out = df.copy()
    out["match_score"] = np.exp(numerator / denominator.replace(0, np.nan)).round(
        ROUNDING_DECIMAL_PLACES
    )
    return out.sort_values(
        ["match_score", "area_id"],
        ascending=[False, True],
        na_position="last",
        kind="stable",
    )


def evidence_quality(
    *,
    available_component_count: int,
    crime_population_denominator: int | None,
    crime_population_reference_date: str | None,
    crime_period_start: str | None,
    crime_period_end: str | None,
    rent_source_grain: str | None,
    rent_reference_date: str | None,
    median_sale_price_confidence: str | None,
    all_component_source_dates_known: bool,
    planning_source_status: str | None,
    flood_source_status: str | None,
) -> str:
    """Executable mirror of the categorical evidence rules in the contract."""
    if (
        available_component_count < 3
        or crime_population_denominator is None
        or planning_source_status != "covered"
        or flood_source_status != "covered"
    ):
        return "limited"
    if (
        available_component_count == 5
        and rent_source_grain == "msoa"
        and median_sale_price_confidence == "reliable"
        and all_component_source_dates_known
        and rent_reference_date is not None
        and crime_population_reference_date is not None
        and crime_period_start is not None
        and crime_period_end is not None
    ):
        return "strong"
    return "mixed"


def price_verdict(asking: float, comparison: float | None) -> tuple[float | None, str]:
    """Return the percentage difference and a neutral comparison band."""
    if comparison is None or pd.isna(comparison) or not comparison:
        return None, "no comparison figure"
    pct = (asking - comparison) / comparison * 100
    if pct < -15:
        band = "well below the comparison figure"
    elif pct < -5:
        band = "below the comparison figure"
    elif pct <= 5:
        band = "about the comparison figure"
    elif pct <= 15:
        band = "above the comparison figure"
    else:
        band = "well above the comparison figure"
    return round(pct, 1), band
