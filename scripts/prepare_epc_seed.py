"""Normalize an EPC bulk download into the energy contract.

The full England & Wales EPC bulk export is large (~6 GB zipped, ~21 GB of
certificates uncompressed across per-year `certificates-YYYY.csv` members) and
gated behind a free GOV.UK One Login, so it is never committed. This helper
streams a local bulk download (a single certificates CSV, or the bulk ZIP whose
members are per-year `certificates-YYYY.csv` files — recommendations are
skipped) into the slim contract used by `stg_epc__certificates`:

  postcode, current_energy_rating, current_energy_efficiency, property_type, lodgement_date

Output defaults to `data/raw/ref_epc_normalized.csv` (gitignored). Load it with
`scripts/load_epc.py`, then build with `--vars 'epc_source: bulk'`.

Usage:
    python scripts/prepare_epc_seed.py path/to/certificates.csv
    python scripts/prepare_epc_seed.py path/to/all-domestic-certificates.zip
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "ref_epc_normalized.csv"

CONTRACT_COLUMNS = [
    "postcode",
    "current_energy_rating",
    "current_energy_efficiency",
    "property_type",
    "lodgement_date",
]

# Logical column -> candidate source headers (compared case-insensitively).
ALIASES = {
    "postcode": ("postcode", "pcds"),
    "current_energy_rating": ("current_energy_rating", "current-energy-rating"),
    "current_energy_efficiency": (
        "current_energy_efficiency",
        "current-energy-efficiency",
    ),
    "property_type": ("property_type", "property-type"),
    "lodgement_date": ("lodgement_date", "lodgement-date", "inspection_date"),
}

CHUNK_SIZE = 500_000


def _resolve(columns: list[str]) -> dict[str, str]:
    lower = {str(column).strip().lower(): column for column in columns}
    resolved: dict[str, str] = {}
    for logical, candidates in ALIASES.items():
        for candidate in candidates:
            if candidate in lower:
                resolved[logical] = lower[candidate]
                break
    missing = [c for c in ("postcode", "current_energy_rating", "current_energy_efficiency") if c not in resolved]
    if missing:
        raise ValueError(f"EPC source is missing required columns: {missing}")
    return resolved


def _is_certificates_member(name: str) -> bool:
    """The bulk ZIP holds per-year certificates-YYYY.csv (plus recommendations we skip)."""
    base = name.rsplit("/", 1)[-1].lower()
    return base.startswith("certificates") and base.endswith(".csv")


def _read_slim_chunks(open_handle):
    """Stream a CSV (via a callable returning a fresh handle) as slim contract chunks.

    Only the contract columns are parsed (usecols) so the 1-2 GB per-year EPC
    files stream in bounded memory instead of materialising all 90+ columns.
    """
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
            chunk = chunk.rename(columns=rename)
            for column in CONTRACT_COLUMNS:
                if column not in chunk.columns:
                    chunk[column] = ""
            chunk = chunk[CONTRACT_COLUMNS]
            yield chunk[chunk["postcode"].astype(str).str.strip() != ""]


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
                    if not info.is_dir() and _is_certificates_member(info.filename)
                ]
                if not members:
                    raise ValueError("No 'certificates*.csv' members found in the EPC ZIP")
                for name in members:
                    print(f"  reading {name}", file=sys.stderr)
                    write(_read_slim_chunks(lambda n=name: archive.open(n)), out_file)
        else:
            write(_read_slim_chunks(lambda: input_path.open("rb")), out_file)

    if not wrote_header:
        raise ValueError("No EPC certificate rows were written")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_path", type=Path, help="EPC certificates CSV or bulk ZIP")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"Default: {DEFAULT_OUTPUT}")
    args = parser.parse_args()

    try:
        rows = prepare(args.input_path, args.output)
    except (OSError, ValueError, zipfile.BadZipFile, pd.errors.ParserError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(f"[done] wrote {rows:,} EPC certificate rows to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
