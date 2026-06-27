"""Extract small ONS name lookups from an ONSPD zip into committed dbt seeds.

Produces three small OGL reference tables (unlike the full multi-million-row
ONSPD postcode file, these are small enough to commit and seed):

  seeds/ref_msoa_names.csv     (area_id, area_name)
  seeds/ref_lad_names.csv      (local_authority_code, local_authority_name)
  seeds/ref_region_names.csv   (region_code, region_name)  -- regions + countries

dim_area and dim_postcode_geography join these to turn raw ONS codes
(E02000001, E09000030, E12000007, W92000004) into readable names
(City of London 001, Tower Hamlets, London, Wales).

Usage:
    python scripts/prepare_geo_name_seeds.py path/to/ONSPD.zip
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"

# Glob patterns are version-tolerant ("...as at 12_21.csv" dates change per release).
MSOA_PATTERN = "Documents/MSOA*names and codes EW*.csv"
LAD_PATTERN = "Documents/LAD*names and codes*.csv"
RGN_PATTERN = "Documents/RGN*names and codes*.csv"
CTRY_PATTERN = "Documents/CTRY*names and codes*.csv"


def _select_member(archive: zipfile.ZipFile, pattern: str) -> str:
    matches = [n for n in archive.namelist() if fnmatch.fnmatch(n, pattern)]
    if not matches:
        raise ValueError(f"No ZIP member matched {pattern!r}")
    return sorted(matches)[0]


def _read_code_name(archive: zipfile.ZipFile, pattern: str) -> pd.DataFrame:
    """Read the first two columns (code, name) of an ONS names-and-codes file."""
    member = _select_member(archive, pattern)
    with archive.open(member) as handle:
        frame = pd.read_csv(handle, dtype=str, keep_default_na=False)
    code_col, name_col = frame.columns[0], frame.columns[1]
    out = frame[[code_col, name_col]].copy()
    out.columns = ["code", "name"]
    out = out[(out["code"].str.strip() != "") & (out["name"].str.strip() != "")]
    return out.drop_duplicates(subset=["code"]).reset_index(drop=True)


def prepare(zip_path: Path) -> list[tuple[Path, int]]:
    written: list[tuple[Path, int]] = []
    with zipfile.ZipFile(zip_path) as archive:
        msoa = _read_code_name(archive, MSOA_PATTERN)
        lad = _read_code_name(archive, LAD_PATTERN)
        # ONSPD uses region pseudo-codes (W99999999 etc.) for the devolved
        # nations, which have no English-style region; map those to the country.
        devolved = pd.DataFrame(
            [
                ("W99999999", "Wales"),
                ("S99999999", "Scotland"),
                ("N99999999", "Northern Ireland"),
                ("L99999999", "Channel Islands"),
                ("M99999999", "Isle of Man"),
            ],
            columns=["code", "name"],
        )
        # Region names cover England's regions; countries + the devolved
        # pseudo-codes resolve everything outside England.
        region = pd.concat(
            [
                _read_code_name(archive, RGN_PATTERN),
                _read_code_name(archive, CTRY_PATTERN),
                devolved,
            ],
            ignore_index=True,
        ).drop_duplicates(subset=["code"])

    targets = [
        (SEEDS / "ref_msoa_names.csv", msoa, ["area_id", "area_name"]),
        (SEEDS / "ref_lad_names.csv", lad, ["local_authority_code", "local_authority_name"]),
        (SEEDS / "ref_region_names.csv", region, ["region_code", "region_name"]),
    ]
    for path, frame, columns in targets:
        frame.columns = columns
        frame.sort_values(columns[0], kind="stable").to_csv(path, index=False)
        written.append((path, len(frame)))
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", type=Path, help="Path to an ONSPD ZIP file.")
    args = parser.parse_args()

    try:
        written = prepare(args.zip_path)
    except (OSError, ValueError, zipfile.BadZipFile, pd.errors.ParserError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    for path, rows in written:
        print(f"[done] wrote {rows:,} rows to {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
