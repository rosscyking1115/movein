"""Spot-check the dashboard-facing reporting marts.

Run any time after `dbt build` to sanity-check that the three rpt_* marts
look right. Useful both during development and after re-running the
ingestion pipeline with a fresh year of Land Registry data.

Usage:
    python scripts/check_marts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"


def fmt_yoy(val: float | None) -> str:
    return f"{val:+.1f}%" if val is not None else "  (n/a)"


def fmt_gbp(val: int | None) -> str:
    return f"GBP{val:>9,}" if val is not None else "      (n/a)"


def main() -> int:
    if not WAREHOUSE.exists():
        print(f"Warehouse not found at {WAREHOUSE}.", file=sys.stderr)
        print("Run `dbt build` first.", file=sys.stderr)
        return 1

    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    latest_year = con.execute(
        """
        select max(transferred_year)
        from main_analytics.rpt_price_yoy_by_region
        """
    ).fetchone()[0]
    if latest_year is None:
        con.close()
        print("No reporting years found in rpt_price_yoy_by_region.", file=sys.stderr)
        return 1

    print("=" * 72)
    print("rpt_price_yoy_by_region — London trajectory")
    print("=" * 72)
    rows = con.execute(
        """
        select transferred_year, sales_count, median_price_gbp, median_yoy_pct
        from main_analytics.rpt_price_yoy_by_region
        where region = ?
        order by transferred_year
        """,
        ["London"],
    ).fetchall()
    for year, n, median, yoy in rows:
        print(
            f"  {year}  n={n:>7,}  median={fmt_gbp(median)}  YoY={fmt_yoy(yoy)}"
        )

    print()
    print("=" * 72)
    print(
        f"rpt_price_yoy_by_region — {latest_year} ranked "
        "(highest median first)"
    )
    print("=" * 72)
    rows = con.execute(
        """
        select region, sales_count, median_price_gbp, median_yoy_pct
        from main_analytics.rpt_price_yoy_by_region
        where transferred_year = ?
        order by median_price_gbp desc
        """,
        [latest_year],
    ).fetchall()
    for region, n, median, yoy in rows:
        print(
            f"  {region:<28} n={n:>7,}  median={fmt_gbp(median)}  YoY={fmt_yoy(yoy)}"
        )

    print()
    print("=" * 72)
    print(f"rpt_top_postcodes_by_volume — top 10 in {latest_year}")
    print("=" * 72)
    rows = con.execute(
        """
        select postcode_area, region, sales_count, median_price_gbp
        from main_analytics.rpt_top_postcodes_by_volume
        where transferred_year = ? and rank_within_year <= 10
        order by rank_within_year
        """,
        [latest_year],
    ).fetchall()
    for area, region, n, median in rows:
        print(
            f"  {area:<5} {region:<28} n={n:>7,}  median={fmt_gbp(median)}"
        )

    print()
    print("=" * 72)
    print(
        f"rpt_new_build_premium — {latest_year} by region "
        "(highest premium first)"
    )
    print("=" * 72)
    rows = con.execute(
        """
        select region, new_build_count, existing_count,
               new_build_median_price_gbp, existing_median_price_gbp,
               premium_pct
        from main_analytics.rpt_new_build_premium
        where transferred_year = ?
        order by premium_pct desc nulls last
        """,
        [latest_year],
    ).fetchall()
    for region, nb_n, ex_n, nb_p, ex_p, prem in rows:
        prem_s = f"{prem:+.1f}%" if prem is not None else " (n/a)"
        print(
            f"  {region:<28} new={nb_n:>5,} existing={ex_n:>7,}  "
            f"new={fmt_gbp(nb_p)}  existing={fmt_gbp(ex_p)}  premium={prem_s}"
        )

    con.close()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
