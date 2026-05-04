"""Download HM Land Registry Price Paid yearly CSVs and convert to Parquet.

Idempotent: if `data/raw/pp-{year}.parquet` already exists, the year is skipped.
Per kit lesson L5, we read the headerless CSV with pandas once, attach a UTC
`_loaded_at` column, and write Snappy Parquet — subsequent dbt runs read the
Parquet (~2s) instead of re-parsing the CSV (~90s for the full file).

Usage:
    python scripts/download_raw.py                # default: 2021-2025 (5 years)
    python scripts/download_raw.py --sample        # latest year only (for CI)
    python scripts/download_raw.py --years 2024 2025

Source: https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads
Data dictionary: https://www.gov.uk/guidance/about-the-price-paid-data
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

LANDREG_BASE = (
    "http://prod.publicdata.landregistry.gov.uk."
    "s3-website-eu-west-1.amazonaws.com"
)

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

# Land Registry Price Paid CSVs are HEADERLESS — column order from the data
# dictionary. Names below are deliberately raw (untransformed) — the staging
# layer in Phase 2 is responsible for renaming and casting.
LANDREG_COLUMNS = [
    "transaction_id",
    "price",
    "date_of_transfer",
    "postcode",
    "property_type",
    "old_new",
    "duration",
    "paon",
    "saon",
    "street",
    "locality",
    "town_city",
    "district",
    "county",
    "ppd_category_type",
    "record_status",
]

# Default: five complete calendar years. 2026 is excluded because at time of
# writing it's a partial year — including it would mess with YoY marts in Phase 3.
DEFAULT_YEARS = [2021, 2022, 2023, 2024, 2025]


def download_year(year: int) -> Path:
    """Download a single year's CSV and convert to Parquet.

    Returns the Parquet path. Skips both the download and the conversion if
    the Parquet file already exists.
    """
    parquet_path = RAW_DIR / f"pp-{year}.parquet"
    csv_path = RAW_DIR / f"pp-{year}.csv"

    if parquet_path.exists():
        size_mb = parquet_path.stat().st_size / 1024 / 1024
        print(f"  [skip]     {parquet_path.name} already present ({size_mb:.1f} MB)")
        return parquet_path

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = f"{LANDREG_BASE}/pp-{year}.csv"
    print(f"  [download] {url}")

    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024  # 1 MB
        with open(csv_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    mb = downloaded // (1024 * 1024)
                    print(f"\r             {pct:3d}% ({mb} MB)", end="", flush=True)
        if total:
            print()  # newline after progress

    print(f"  [convert]  {csv_path.name} → {parquet_path.name}")
    df = pd.read_csv(
        csv_path,
        names=LANDREG_COLUMNS,
        header=None,
        dtype=str,                 # keep everything as text — staging casts.
        keep_default_na=False,
        na_values=[""],
        encoding="utf-8",
        low_memory=False,
    )
    df["_loaded_at"] = datetime.now(timezone.utc).isoformat()

    df.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=False)

    # Drop the CSV after successful conversion (kit lesson L5 — disk hygiene).
    csv_path.unlink(missing_ok=True)

    rows = len(df)
    size_mb = parquet_path.stat().st_size / 1024 / 1024
    print(f"  [done]     {rows:,} rows → {size_mb:.1f} MB Parquet")
    return parquet_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--sample",
        action="store_true",
        help="Download only the most recent year — used by CI for fast runs.",
    )
    group.add_argument(
        "--years",
        nargs="+",
        type=int,
        metavar="YEAR",
        help="Specific years to fetch, e.g. --years 2024 2025.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.sample:
        years = [max(DEFAULT_YEARS)]
    elif args.years:
        years = sorted(set(args.years))
    else:
        years = DEFAULT_YEARS

    print(f"Land Registry Price Paid — fetching years: {years}")
    print(f"Output dir: {RAW_DIR}")
    print()

    for year in years:
        try:
            download_year(year)
        except requests.HTTPError as e:
            print(f"\n  [error]    Failed to fetch {year}: {e}", file=sys.stderr)
            return 1
        except requests.RequestException as e:
            print(f"\n  [error]    Network error for {year}: {e}", file=sys.stderr)
            return 1

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
