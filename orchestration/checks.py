"""The ingestion gate — asset checks dbt can't do.

dbt tests run *after* data lands in the warehouse. These checks run on the raw
parquet *before* it is loaded, so a bad monthly drop (a truncated file, a null
flood, a wave of malformed postcodes) is caught at the front door instead of
silently propagating into the marts. They are blocking: a failure stops the
graph before warehouse_transactions runs.
"""

import duckdb
from dagster import AssetCheckExecutionContext, AssetCheckResult, asset_check

from .ingest_assets import raw_landreg_ppd
from .resources import RAW_GLOB

# A full monthly Land Registry drop for the 2021–2025 window is ~5M rows. A
# result far below this means a truncated or partial file — fail loudly.
MIN_EXPECTED_ROWS = 3_000_000

# Postcodes are legitimately empty for some old records, so we gate on the rate
# of *malformed non-empty* postcodes, not on emptiness. A UK postcode looks like
# "SW1A 1AA" / "M1 1AE"; a small malformed fraction is normal source noise.
MAX_MALFORMED_POSTCODE_PCT = 1.0

UK_POSTCODE_RE = r"^[A-Z]{1,2}[0-9][0-9A-Z]? ?[0-9][A-Z]{2}$"


@asset_check(
    asset=raw_landreg_ppd,
    blocking=True,
    description=(
        "Row-count floor, price/date null-flood, and malformed-postcode rate on "
        "the raw PPD parquet before it enters the warehouse."
    ),
)
def raw_landreg_ppd_is_sane(
    context: AssetCheckExecutionContext,
) -> AssetCheckResult:
    con = duckdb.connect(":memory:")
    try:
        con.execute(
            f"create view ppd as select * from read_parquet('{RAW_GLOB}')"
        )
        total = con.execute("select count(*) from ppd").fetchone()[0]
        null_price = con.execute(
            "select count(*) from ppd where price is null or price = ''"
        ).fetchone()[0]
        null_date = con.execute(
            "select count(*) from ppd where date_of_transfer is null"
        ).fetchone()[0]
        malformed_pc = con.execute(
            f"""
            select count(*) from ppd
            where postcode is not null and postcode <> ''
              and not regexp_matches(upper(trim(postcode)), '{UK_POSTCODE_RE}')
            """
        ).fetchone()[0]
    finally:
        con.close()

    malformed_pct = (malformed_pc / total * 100) if total else 0.0

    passed = (
        total >= MIN_EXPECTED_ROWS
        and null_price == 0
        and null_date == 0
        and malformed_pct <= MAX_MALFORMED_POSTCODE_PCT
    )

    return AssetCheckResult(
        passed=passed,
        metadata={
            "row_count": total,
            "min_expected_rows": MIN_EXPECTED_ROWS,
            "null_price": null_price,
            "null_date": null_date,
            "malformed_postcode_count": malformed_pc,
            "malformed_postcode_pct": round(malformed_pct, 3),
            "max_malformed_postcode_pct": MAX_MALFORMED_POSTCODE_PCT,
        },
    )
