"""Extract the latest ONS Price Index of Private Rents (PIPR) levels into a seed.

The PIPR release is a large monthly time series (one row per area per month).
This helper pulls the latest month's average monthly rent (GBP) for every
England & Wales geography and writes the small committed seed:

  seeds/ref_ons_rent.csv  (area_code, area_name, rent_grain, rent_monthly_gbp,
                           rent_1bed_gbp, rent_2bed_gbp, rent_3bed_gbp,
                           rent_4plus_gbp, rent_period)

rent_grain is local_authority (E06-E09 / W06), region (E12) or country (E92/W92),
so the area profile can fall back from finest to coarsest available rent.

Source: ONS, Price Index of Private Rents, UK: monthly price statistics
        https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics
Licence: Open Government Licence v3.0. Latest values may be provisional.

Usage:
    python scripts/prepare_ons_rent_seed.py path/to/pipr.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "seeds" / "ref_ons_rent.csv"
SHEET = "Table 1"

# England & Wales area-code prefixes → rent grain. Scotland/NI and the UK
# aggregate are dropped: this product covers England & Wales (matching Land
# Registry), and finer grains are preferred when available.
GRAIN_BY_PREFIX = {
    "E06": "local_authority",
    "E07": "local_authority",
    "E08": "local_authority",
    "E09": "local_authority",
    "W06": "local_authority",
    "E12": "region",
    "E92": "country",
    "W92": "country",
}


def prepare(xlsx_path: Path) -> int:
    frame = pd.read_excel(xlsx_path, sheet_name=SHEET, header=2)
    frame.columns = [str(column).strip() for column in frame.columns]

    required = ["Time period", "Area code", "Area name", "Rental price"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"PIPR sheet is missing expected columns: {missing}")

    latest_period = frame["Time period"].max()
    latest = frame[frame["Time period"] == latest_period].copy()

    latest["rent_grain"] = latest["Area code"].astype(str).str[:3].map(GRAIN_BY_PREFIX)
    latest = latest[latest["rent_grain"].notna()]
    latest = latest[pd.to_numeric(latest["Rental price"], errors="coerce").notna()]

    def _rent(column: str) -> pd.Series:
        # Per-bedroom prices can be suppressed (blank) for small samples; keep
        # them nullable rather than dropping the row.
        if column not in latest.columns:
            return pd.Series([pd.NA] * len(latest), index=latest.index)
        return pd.to_numeric(latest[column], errors="coerce").round()

    out = pd.DataFrame(
        {
            "area_code": latest["Area code"].astype(str).str.strip(),
            "area_name": latest["Area name"].astype(str).str.strip(),
            "rent_grain": latest["rent_grain"],
            "rent_monthly_gbp": pd.to_numeric(latest["Rental price"]).round().astype(int),
            "rent_1bed_gbp": _rent("Rental price one bed"),
            "rent_2bed_gbp": _rent("Rental price two bed"),
            "rent_3bed_gbp": _rent("Rental price three bed"),
            "rent_4plus_gbp": _rent("Rental price four or more bed"),
            "rent_period": pd.to_datetime(latest_period).date().isoformat(),
        }
    )
    out = out.drop_duplicates(subset=["area_code"]).sort_values("area_code", kind="stable")
    out.to_csv(OUTPUT, index=False)
    return len(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx_path", type=Path, help="Path to the PIPR monthly price statistics .xlsx")
    args = parser.parse_args()

    try:
        rows = prepare(args.xlsx_path)
    except (OSError, ValueError, KeyError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(f"[done] wrote {rows:,} England & Wales rent rows to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
