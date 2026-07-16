"""Recompute the neighbourhood scores in data/decision.duckdb.

The scoring redesign (replacing percentile rank with magnitude-preserving,
median-anchored winsorised min-max + absolute EPC/flood anchors, aggregated by a
weighted GEOMETRIC mean) is a pure function of the raw facts in
app.rpt_area_profile_mvp — which the committed extract already holds for all
7,264 areas. So we can regenerate app.rpt_neighbourhood_score in place without a
full warehouse rebuild. The dbt model models/marts/decision/rpt_neighbourhood_score.sql
implements the same logic for full real rebuilds; keep the two in sync.

Method (per indicator → 0-100, higher = better):
  - affordability (rent-to-income, lower better), recorded crime (rate, lower
    better), convenience-station (km, lower better): median-anchored winsorised
    min-max — clip to [p2, p98], map p2→0/100, median→50, p98→100/0. This puts
    the typical area at 50 and keeps magnitude (unlike percentile rank).
  - energy: absolute EPC anchor A=100 B=83 C=67 D=50 E=33 F=17 G=0.
  - flood: absolute, 100 - flood_postcode_pct (share of postcodes in a flood zone).
  - convenience: mean of walkable (count/5 * 100) and the station score.
  - overall: weighted GEOMETRIC mean of the available components (floor 1), so a
    single excellent pillar can't mask a terrible one.

Usage:
    python scripts/rescore_extract.py            # rewrite data/decision.duckdb
    python scripts/rescore_extract.py --verify   # print before/after, write nothing
    python scripts/rescore_extract.py --db PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "decision.duckdb"
CONTRACT = json.loads((ROOT / "contracts" / "neighbourhood-scoring-v2.json").read_text())
CONTRACT_VERSION = CONTRACT["schema_version"]

# Equal default weights; the website re-weights client-side from the components.
WEIGHTS = {
    name.removesuffix("_score"): float(config["default_weight"])
    for name, config in CONTRACT["components"].items()
}

# Median-anchored winsorised min-max for a higher-is-better value (0-100).
def _mab(col: str, lo: str, md: str, hi: str) -> str:
    clip = f"least(greatest({col}, {lo}), {hi})"
    return (
        f"case when {col} is null then null "
        f"when {clip} <= {md} then 50.0 * ({clip} - {lo}) / nullif({md} - {lo}, 0) "
        f"else 50.0 + 50.0 * ({clip} - {md}) / nullif({hi} - {md}, 0) end"
    )


def _lower_better(col: str, lo: str, md: str, hi: str) -> str:
    return f"100.0 - ({_mab(col, lo, md, hi)})"


SCORE_SQL = f"""
with p as (select * from app.rpt_area_profile_mvp),
b as (
    select
        quantile_cont(affordability_ratio, 0.02) as aff_lo,
        median(affordability_ratio)              as aff_md,
        quantile_cont(affordability_ratio, 0.98) as aff_hi,
        quantile_cont(crime_rate_per_1000, 0.02) as cr_lo,
        median(crime_rate_per_1000)              as cr_md,
        quantile_cont(crime_rate_per_1000, 0.98) as cr_hi,
        quantile_cont(nearest_station_km, 0.02)  as st_lo,
        median(nearest_station_km)               as st_md,
        quantile_cont(nearest_station_km, 0.98)  as st_hi
    from p
),
raw as (
    select
        p.area_id, p.area_name, p.local_authority_name, p.region,
        p.rent_source_grain, p.rent_reference_date, p.median_sale_price_confidence,
        p.crime_population_denominator, p.crime_population_reference_date,
        p.crime_period_start, p.crime_period_end, p.planning_source_status,
        p.flood_source_status,
        false as all_component_source_dates_known,
        case when p.affordability_ratio is not null then
            round(greatest(0, least(100, {_lower_better('p.affordability_ratio', 'b.aff_lo', 'b.aff_md', 'b.aff_hi')})), 1)
        end as affordability_score,
        case when p.crime_rate_per_1000 is not null then
            round(greatest(0, least(100, {_lower_better('p.crime_rate_per_1000', 'b.cr_lo', 'b.cr_md', 'b.cr_hi')})), 1)
        end as safety_score,
        case p.epc_median_rating
            when 'A' then 100.0 when 'B' then 83.0 when 'C' then 67.0
            when 'D' then 50.0 when 'E' then 33.0 when 'F' then 17.0 when 'G' then 0.0
        end as energy_score,
        case when p.flood_postcode_pct is not null
            then round(greatest(0, least(100, 100.0 - p.flood_postcode_pct)), 1) end as flood_score,
        -- convenience: walkable essentials (count/5) blended with station proximity
        case
            when p.walkable_amenity_count is null then null
            when p.nearest_station_km is not null then round(greatest(0, least(100, (
                (100.0 * p.walkable_amenity_count / 5.0)
                + greatest(0, least(100, {_lower_better('p.nearest_station_km', 'b.st_lo', 'b.st_md', 'b.st_hi')}))
            ) / 2.0)), 1)
            else round(greatest(0, least(100, 100.0 * p.walkable_amenity_count / 5.0)), 1)
        end as convenience_score
    from p, b
),
scored as (
    select *,
        (case when affordability_score is not null then 1 else 0 end
         + case when safety_score is not null then 1 else 0 end
         + case when energy_score is not null then 1 else 0 end
         + case when flood_score is not null then 1 else 0 end
         + case when convenience_score is not null then 1 else 0 end) as components_available,
        -- weighted geometric mean of available components, floor 1 (anti-cancellation)
        round(exp(
            (
                coalesce({WEIGHTS['affordability']} * ln(greatest(affordability_score, 1)), 0)
                + coalesce({WEIGHTS['safety']} * ln(greatest(safety_score, 1)), 0)
                + coalesce({WEIGHTS['energy']} * ln(greatest(energy_score, 1)), 0)
                + coalesce({WEIGHTS['flood']} * ln(greatest(flood_score, 1)), 0)
                + coalesce({WEIGHTS['convenience']} * ln(greatest(convenience_score, 1)), 0)
            ) / nullif(
                (case when affordability_score is not null then {WEIGHTS['affordability']} else 0 end)
                + (case when safety_score is not null then {WEIGHTS['safety']} else 0 end)
                + (case when energy_score is not null then {WEIGHTS['energy']} else 0 end)
                + (case when flood_score is not null then {WEIGHTS['flood']} else 0 end)
                + (case when convenience_score is not null then {WEIGHTS['convenience']} else 0 end), 0)
        ), 1) as overall_score
    from raw
)
select
    area_id, area_name, local_authority_name, region,
    affordability_score, safety_score, energy_score, flood_score, convenience_score,
    overall_score,
    dense_rank() over (order by overall_score desc nulls last) as overall_rank,
    components_available as available_component_count,
    5 as expected_component_count,
    all_component_source_dates_known,
    case
        when components_available < 3
            or crime_population_denominator is null
            or flood_source_status is distinct from 'covered'
            or planning_source_status is distinct from 'covered' then 'limited'
        when components_available = 5
            and rent_source_grain = 'msoa'
            and median_sale_price_confidence = 'reliable'
            and all_component_source_dates_known
            and rent_reference_date is not null
            and crime_population_reference_date is not null
            and crime_period_start is not null
            and crime_period_end is not null then 'strong'
        else 'mixed'
    end as evidence_quality_level,
    case
        when components_available < 3 then concat(
            'Limited evidence: only ', components_available, ' of 5 scored indicators are available.')
        when crime_population_denominator is null then
            'Limited evidence: a compatible population denominator is unavailable for the crime indicator.'
        when flood_source_status is distinct from 'covered'
            or planning_source_status is distinct from 'covered' then
            'Limited evidence: planning or flood coverage is unavailable for this jurisdiction.'
        when affordability_score is null then
            'Mixed evidence: the rent indicator is unavailable for this neighbourhood.'
        when rent_source_grain is distinct from 'msoa' then
            'Mixed evidence: all available scores are shown, but rent is local-authority context rather than neighbourhood-level evidence.'
        when median_sale_price_confidence is distinct from 'reliable' then
            'Mixed evidence: the latest-year sale-price evidence is unavailable or not based on a reliable sample.'
        when not all_component_source_dates_known then
            'Mixed evidence: dated provenance is not available for every scored component.'
        when rent_reference_date is null
            or crime_population_reference_date is null
            or crime_period_start is null
            or crime_period_end is null then
            'Mixed evidence: one or more source reference periods are unavailable.'
        else 'Strong evidence: all five scored indicators have compatible coverage and dated provenance.'
    end as evidence_quality_notes,
    concat('Strongest on ',
        case greatest(affordability_score, safety_score, energy_score, flood_score, convenience_score)
            when affordability_score then 'affordability' when safety_score then 'recorded crime'
            when energy_score then 'energy efficiency' when flood_score then 'low flood risk'
            else 'convenience' end,
        ', weakest on ',
        case least(affordability_score, safety_score, energy_score, flood_score, convenience_score)
            when affordability_score then 'affordability' when safety_score then 'recorded crime'
            when energy_score then 'energy efficiency' when flood_score then 'flood risk'
            else 'convenience' end,
        '. Overall combines ', components_available, ' of 5 indicators.') as why_this_area
from scored
order by overall_score desc nulls last, area_id asc
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--verify", action="store_true", help="print stats, write nothing")
    args = ap.parse_args()

    con = duckdb.connect(args.db, read_only=args.verify)
    new = con.execute(SCORE_SQL).df()

    def dist(s):
        return f"min {s.min():.1f} · p25 {s.quantile(.25):.1f} · median {s.median():.1f} · p75 {s.quantile(.75):.1f} · max {s.max():.1f}"

    print(f"Rescored {len(new):,} areas.")
    for c in ["affordability_score", "safety_score", "energy_score", "flood_score", "convenience_score", "overall_score"]:
        print(f"  {c:20} {dist(new[c].dropna())}")

    if not args.verify:
        con.execute("create or replace table app.rpt_neighbourhood_score as " + SCORE_SQL)
        con.close()
        print(f"\nWrote app.rpt_neighbourhood_score to {args.db}")
    else:
        con.close()
        print("\n(verify mode — nothing written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
