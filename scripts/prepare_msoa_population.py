"""Normalize the ONS mid-2024 MSOA population workbook into a dbt seed.

The source is the accredited official-statistics workbook for 2021 MSOAs in
England and Wales. The resulting seed supplies the compatible resident
population denominator used by the recorded-crime indicator.

Usage:
    python scripts/prepare_msoa_population.py data/raw/sapemsoaquinaryage20222024.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "seeds" / "ref_msoa_population.csv"
SHEET_NAME = "Mid-2024 MSOA 2021"
REFERENCE_DATE = "2024-06-30"
GEOGRAPHY_VERSION = "MSOA 2021"
SOURCE_NAME = "ONS Middle layer Super Output Area population estimates, mid-2024"
SOURCE_URL = (
    "https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/"
    "populationestimates/datasets/middlesuperoutputareamidyearpopulationestimatesnationalstatistics"
)
SOURCE_RELEASE_DATE = "2025-11-07"
CONTRACT_COLUMNS = [
    "area_id",
    "area_name",
    "population",
    "population_reference_date",
    "geography_version",
    "source_name",
    "source_url",
    "source_release_date",
]


def normalize_population(frame: pd.DataFrame) -> pd.DataFrame:
    """Return one validated population row per England/Wales 2021 MSOA."""
    required = {"MSOA 2021 Code", "MSOA 2021 Name", "Total"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing ONS population column(s): {', '.join(missing)}")

    result = pd.DataFrame(
        {
            "area_id": frame["MSOA 2021 Code"].astype("string").str.strip(),
            "area_name": frame["MSOA 2021 Name"].astype("string").str.strip(),
            "population": pd.to_numeric(
                frame["Total"].astype("string").str.replace(",", "", regex=False),
                errors="coerce",
            ),
        }
    )
    result = result[result["area_id"].str.fullmatch(r"[EW]\d{8}", na=False)].copy()
    if (
        result.empty
        or result["area_id"].duplicated().any()
        or result["population"].isna().any()
        or (result["population"] <= 0).any()
    ):
        raise ValueError("ONS MSOA rows must have a unique positive population")

    result["population"] = result["population"].astype("int64")
    result["population_reference_date"] = REFERENCE_DATE
    result["geography_version"] = GEOGRAPHY_VERSION
    result["source_name"] = SOURCE_NAME
    result["source_url"] = SOURCE_URL
    result["source_release_date"] = SOURCE_RELEASE_DATE
    return result[CONTRACT_COLUMNS].sort_values("area_id").reset_index(drop=True)


def prepare(workbook_path: Path, output_path: Path = OUTPUT) -> int:
    frame = pd.read_excel(workbook_path, sheet_name=SHEET_NAME, header=3)
    result = normalize_population(frame)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return len(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path, help="Downloaded ONS population workbook")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    try:
        rows = prepare(args.workbook, args.output)
    except (OSError, ValueError, KeyError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    print(f"[done] wrote {rows:,} MSOA population rows to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
