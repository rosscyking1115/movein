"""Normalize a data.police.uk bulk crime archive into the crime contract.

The bulk download is a ZIP of per-month folders, each holding per-force
`YYYY-MM-<force>-street.csv` files (outcomes / stop-and-search are skipped).
This helper streams the street files into the slim contract used by
`stg_crime__street`:

  lsoa_code, crime_type, month

Output defaults to `data/raw/ref_crime_normalized.csv` (gitignored). Load it with
`scripts/load_crime.py`, then build with `--vars 'crime_source: bulk'`.

Source: https://data.police.uk/data/ (Open Government Licence v3.0). England &
Wales + British Transport Police; indicators only, never a safe/unsafe label.

Usage:
    python scripts/prepare_crime_seed.py path/to/police-bulk.zip
    python scripts/prepare_crime_seed.py path/to/2026-04-metropolitan-street.csv
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "ref_crime_normalized.csv"

CONTRACT_COLUMNS = ["lsoa_code", "crime_type", "month"]

# Logical column -> candidate source headers (compared after normalising any
# non-alphanumeric run to a single underscore, so "LSOA code" -> "lsoa_code").
ALIASES = {
    "lsoa_code": ("lsoa_code", "lsoa"),
    "crime_type": ("crime_type",),
    "month": ("month",),
}

CHUNK_SIZE = 500_000


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def _resolve(columns: list[str]) -> dict[str, str]:
    normalised = {_norm(column): column for column in columns}
    resolved: dict[str, str] = {}
    for logical, candidates in ALIASES.items():
        for candidate in candidates:
            if candidate in normalised:
                resolved[logical] = normalised[candidate]
                break
    missing = [c for c in CONTRACT_COLUMNS if c not in resolved]
    if missing:
        raise ValueError(f"Police crime source is missing required columns: {missing}")
    return resolved


def _is_street_member(name: str) -> bool:
    return name.rsplit("/", 1)[-1].lower().endswith("street.csv")


def _read_slim_chunks(open_handle):
    with open_handle() as handle:
        header = pd.read_csv(handle, nrows=0, dtype=str)
    resolved = _resolve(list(header.columns))
    rename = {source: logical for logical, source in resolved.items()}

    with open_handle() as handle:
        for chunk in pd.read_csv(
            handle,
            dtype=str,
            keep_default_na=False,
            low_memory=False,
            usecols=list(resolved.values()),
            chunksize=CHUNK_SIZE,
        ):
            chunk = chunk.rename(columns=rename)[CONTRACT_COLUMNS]
            yield chunk[chunk["lsoa_code"].astype(str).str.strip() != ""]


def prepare(input_path: Path, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    wrote_header = False

    def write(chunks, out_file):
        nonlocal rows, wrote_header
        for chunk in chunks:
            if chunk.empty:
                continue
            chunk.to_csv(out_file, index=False, header=not wrote_header)
            wrote_header = True
            rows += len(chunk)

    with output_path.open("w", encoding="utf-8", newline="") as out_file:
        if input_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(input_path) as archive:
                members = [
                    info.filename
                    for info in archive.infolist()
                    if not info.is_dir() and _is_street_member(info.filename)
                ]
                if not members:
                    raise ValueError("No '*street.csv' members found in the police ZIP")
                for name in members:
                    write(_read_slim_chunks(lambda n=name: archive.open(n)), out_file)
        else:
            write(_read_slim_chunks(lambda: input_path.open("rb")), out_file)

    if not wrote_header:
        raise ValueError("No crime rows were written")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_path", type=Path, help="Police bulk ZIP or a single street CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"Default: {DEFAULT_OUTPUT}")
    args = parser.parse_args()

    try:
        rows = prepare(args.input_path, args.output)
    except (OSError, ValueError, zipfile.BadZipFile, pd.errors.ParserError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(f"[done] wrote {rows:,} crime rows to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
