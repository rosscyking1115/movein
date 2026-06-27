"""Normalize an official postcode lookup CSV/ZIP into the housing geography contract.

The committed `seeds/ref_onspd_sample.csv` is intentionally tiny so CI stays
fast. This helper lets a real ONSPD-style snapshot be prepared locally without
committing the large upstream file.

Usage:
    python scripts/prepare_onspd_seed.py path/to/onspd.csv
    python scripts/prepare_onspd_seed.py path/to/onspd.zip --member Data/*.csv
    python scripts/prepare_onspd_seed.py path/to/onspd.zip --limit 1000 --output seeds/ref_onspd_sample.csv
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "ref_onspd_normalized.csv"
DEFAULT_SOURCE_NAME = "ONS Postcode Directory"
DEFAULT_SOURCE_URL = "https://geoportal.statistics.gov.uk/"

CONTRACT_COLUMNS = [
    "postcode",
    "postcode_outward",
    "postcode_area",
    "area_id",
    "area_name",
    "lsoa_code",
    "local_authority_code",
    "local_authority_name",
    "region",
    "latitude",
    "longitude",
    "is_current_postcode",
    "source_snapshot_date",
    "source_name",
    "source_url",
]

COLUMN_ALIASES = {
    "postcode": ("postcode", "pcds", "pcd", "pcd2"),
    "area_id": ("area_id", "msoa_code", "msoa", "msoa21", "msoa11"),
    "area_name": ("area_name", "msoa_name", "msoa21nm", "msoa11nm"),
    "lsoa_code": ("lsoa_code", "lsoa", "lsoa21", "lsoa11"),
    "local_authority_code": (
        "local_authority_code",
        "oslaua",
        "ladcd",
        "lad23cd",
        "lad22cd",
    ),
    "local_authority_name": (
        "local_authority_name",
        "ladnm",
        "lad23nm",
        "lad22nm",
        "oslaunm",
    ),
    "region": ("region", "rgn", "rgn23cd", "rgn22cd"),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "long", "longwgs"),
    "termination_date": ("termination_date", "doterm", "dotermdate"),
}

# Regex fallbacks for the ONS date-stamped column convention used since ~2024
# (e.g. msoa21cd, lsoa21cd, lad25cd, rgn25cd). Tried after the exact aliases
# above. The capture group is a vintage/year — when several columns match
# (msoa01cd / msoa11cd / msoa21cd), the highest is preferred so we pick the
# current census or release vintage automatically as new years ship.
COLUMN_PATTERNS = {
    "area_id": (r"^msoa(\d{2})cd$", r"^msoa(\d{2})$"),
    "area_name": (r"^msoa(\d{2})nm$",),
    "lsoa_code": (r"^lsoa(\d{2})cd$", r"^lsoa(\d{2})$"),
    "local_authority_code": (r"^lad(\d{2})cd$", r"^laua(\d{2})cd$"),
    "local_authority_name": (r"^lad(\d{2})nm$", r"^laua(\d{2})nm$"),
    "region": (r"^rgn(\d{2})cd$", r"^gor(\d{2})cd$"),
}

REQUIRED_LOGICAL_COLUMNS = (
    "postcode",
    "area_id",
    "lsoa_code",
    "local_authority_code",
    "latitude",
    "longitude",
)


@dataclass(frozen=True)
class PrepareResult:
    """Summary of the normalized file written by the helper."""

    output_path: Path
    rows_written: int
    source_member: str | None = None


def _normalise_column_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def _normalised_columns(columns: list[str]) -> dict[str, str]:
    return {_normalise_column_name(column): column for column in columns}


def _resolve_column(
    columns: list[str],
    logical_name: str,
    overrides: dict[str, str] | None = None,
    *,
    required: bool = False,
) -> str | None:
    normalised = _normalised_columns(columns)

    if overrides and logical_name in overrides and overrides[logical_name]:
        override = _normalise_column_name(overrides[logical_name])
        if override not in normalised:
            raise ValueError(
                f"Column override for {logical_name!r} points to missing column "
                f"{overrides[logical_name]!r}"
            )
        return normalised[override]

    for alias in COLUMN_ALIASES[logical_name]:
        match = normalised.get(_normalise_column_name(alias))
        if match:
            return match

    candidates: list[tuple[int, str]] = []
    for pattern in COLUMN_PATTERNS.get(logical_name, ()):
        for normed, original in normalised.items():
            found = re.match(pattern, normed)
            if found:
                vintage = int(found.group(1)) if found.groups() else -1
                candidates.append((vintage, original))
    if candidates:
        return max(candidates, key=lambda item: item[0])[1]

    if required:
        aliases = ", ".join(COLUMN_ALIASES[logical_name])
        raise ValueError(
            f"Could not find required {logical_name!r} column. Tried aliases: {aliases}"
        )
    return None


def _format_postcode(value: object) -> str:
    if pd.isna(value):
        return ""

    compact = re.sub(r"\s+", "", str(value).strip().upper())
    if not compact:
        return ""
    if len(compact) <= 3:
        return compact
    return f"{compact[:-3]} {compact[-3:]}"


def _postcode_outward(postcode: str) -> str:
    return postcode.split(" ", 1)[0] if postcode else ""


def _postcode_area(postcode: str) -> str:
    match = re.match(r"^[A-Z]+", postcode)
    return match.group(0) if match else ""


def _clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _is_current_postcode(value: object) -> str:
    termination_date = _clean_text(value)
    return "true" if termination_date == "" else "false"


def _candidate_zip_members(zip_path: Path) -> list[zipfile.ZipInfo]:
    with zipfile.ZipFile(zip_path) as archive:
        return [
            info
            for info in archive.infolist()
            if not info.is_dir() and info.filename.lower().endswith(".csv")
        ]


def select_zip_member(zip_path: Path, member_pattern: str | None = None) -> str:
    """Choose the CSV member to read from a ZIP archive."""
    candidates = _candidate_zip_members(zip_path)
    if not candidates:
        raise ValueError(f"No CSV files found in {zip_path}")

    if member_pattern:
        matches = [
            info
            for info in candidates
            if info.filename == member_pattern or fnmatch.fnmatch(info.filename, member_pattern)
        ]
        if not matches:
            available = ", ".join(info.filename for info in candidates[:10])
            raise ValueError(
                f"No ZIP member matched {member_pattern!r}. Available CSV files: {available}"
            )
        if len(matches) > 1:
            names = ", ".join(info.filename for info in matches[:10])
            raise ValueError(f"ZIP member pattern {member_pattern!r} matched multiple files: {names}")
        return matches[0].filename

    return max(candidates, key=lambda info: info.file_size).filename


def read_lookup(path: Path, *, member: str | None = None) -> tuple[pd.DataFrame, str | None]:
    """Read a CSV or one CSV member from a ZIP archive as strings."""
    if path.suffix.lower() == ".zip":
        selected_member = select_zip_member(path, member)
        with zipfile.ZipFile(path) as archive:
            with archive.open(selected_member) as csv_file:
                return (
                    pd.read_csv(csv_file, dtype=str, keep_default_na=False, low_memory=False),
                    selected_member,
                )

    return (
        pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False),
        None,
    )


def normalize_lookup(
    lookup: pd.DataFrame,
    *,
    snapshot_date: str,
    source_name: str = DEFAULT_SOURCE_NAME,
    source_url: str = DEFAULT_SOURCE_URL,
    limit: int | None = None,
    overrides: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Normalize an ONSPD-shaped dataframe to `ref_onspd_sample` columns."""
    columns = list(lookup.columns)
    resolved = {
        logical_name: _resolve_column(
            columns,
            logical_name,
            overrides,
            required=logical_name in REQUIRED_LOGICAL_COLUMNS,
        )
        for logical_name in COLUMN_ALIASES
    }

    output = pd.DataFrame()
    output["postcode"] = lookup[resolved["postcode"]].map(_format_postcode)
    output["postcode_outward"] = output["postcode"].map(_postcode_outward)
    output["postcode_area"] = output["postcode"].map(_postcode_area)

    for target in (
        "area_id",
        "area_name",
        "lsoa_code",
        "local_authority_code",
        "local_authority_name",
        "region",
        "latitude",
        "longitude",
    ):
        source_column = resolved[target]
        output[target] = lookup[source_column].map(_clean_text) if source_column else ""

    output["area_name"] = output["area_name"].where(output["area_name"] != "", output["area_id"])
    output["local_authority_name"] = output["local_authority_name"].where(
        output["local_authority_name"] != "",
        output["local_authority_code"],
    )

    termination_column = resolved["termination_date"]
    output["is_current_postcode"] = (
        lookup[termination_column].map(_is_current_postcode) if termination_column else "true"
    )
    output["source_snapshot_date"] = snapshot_date
    output["source_name"] = source_name
    output["source_url"] = source_url

    output = output[CONTRACT_COLUMNS]
    output = output[output["postcode"] != ""].drop_duplicates(subset=["postcode"])
    output = output.sort_values("postcode", kind="stable")

    if limit is not None:
        output = output.head(limit)

    return output.reset_index(drop=True)


def prepare_seed(
    input_path: Path,
    output_path: Path,
    *,
    snapshot_date: str,
    source_name: str = DEFAULT_SOURCE_NAME,
    source_url: str = DEFAULT_SOURCE_URL,
    member: str | None = None,
    limit: int | None = None,
    overrides: dict[str, str] | None = None,
) -> PrepareResult:
    lookup, selected_member = read_lookup(input_path, member=member)
    normalized = normalize_lookup(
        lookup,
        snapshot_date=snapshot_date,
        source_name=source_name,
        source_url=source_url,
        limit=limit,
        overrides=overrides,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(output_path, index=False)

    return PrepareResult(
        output_path=output_path,
        rows_written=len(normalized),
        source_member=selected_member,
    )


def _parse_overrides(values: list[str] | None) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for value in values or []:
        logical_name, separator, source_column = value.partition("=")
        if separator != "=" or not logical_name or not source_column:
            raise ValueError(
                "Column overrides must use LOGICAL_NAME=SOURCE_COLUMN, "
                "for example --column area_id=msoa21"
            )
        if logical_name not in COLUMN_ALIASES:
            raise ValueError(f"Unknown logical column override {logical_name!r}")
        overrides[logical_name] = source_column
    return overrides


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_path", type=Path, help="Path to an ONSPD-style CSV or ZIP file.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Normalized CSV output path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--snapshot-date",
        required=True,
        help="Official lookup snapshot date to stamp on every row, e.g. 2026-05-01.",
    )
    parser.add_argument(
        "--source-name",
        default=DEFAULT_SOURCE_NAME,
        help=f"Source label to stamp on every row. Default: {DEFAULT_SOURCE_NAME}",
    )
    parser.add_argument(
        "--source-url",
        default=DEFAULT_SOURCE_URL,
        help=f"Source URL to stamp on every row. Default: {DEFAULT_SOURCE_URL}",
    )
    parser.add_argument(
        "--member",
        help="CSV member name or glob pattern when input_path is a ZIP.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional row limit for creating a small fixture from a full lookup.",
    )
    parser.add_argument(
        "--column",
        action="append",
        help=(
            "Override source-column detection with LOGICAL_NAME=SOURCE_COLUMN. "
            "Can be repeated."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        overrides = _parse_overrides(args.column)
        result = prepare_seed(
            args.input_path,
            args.output,
            snapshot_date=args.snapshot_date,
            source_name=args.source_name,
            source_url=args.source_url,
            member=args.member,
            limit=args.limit,
            overrides=overrides,
        )
    except (OSError, ValueError, zipfile.BadZipFile, pd.errors.ParserError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    member_text = f" from ZIP member {result.source_member}" if result.source_member else ""
    print(f"[done] wrote {result.rows_written:,} rows{member_text} to {result.output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
