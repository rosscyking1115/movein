{{
    config(
        materialized='table'
    )
}}

-- Explainable neighbourhood scoring (redesigned).
--
-- Each component is a 0-100 score where 50 ≈ the typical England & Wales area.
-- Continuous indicators use a MEDIAN-ANCHORED WINSORISED MIN-MAX (clip to the
-- 2nd/98th percentile, map p2->0, median->50, p98->100), which preserves
-- magnitude — unlike a pure percentile rank, which forces a uniform 0-100 spread
-- and makes every area look extreme. Categorical/absolute indicators use fixed
-- anchors (EPC band; flood = share of postcodes in a flood zone). The overall is
-- a weighted GEOMETRIC mean of the components an area has (floored at 1), so a
-- single excellent pillar cannot mask a poor one. A missing component lowers
-- confidence and is dropped, never scored zero.
--
-- The committed data/decision.duckdb is regenerated with the identical method by
-- scripts/rescore_extract.py (it can rescore the extract without a full rebuild);
-- keep the two in sync.

with profile as (

    select * from {{ ref('rpt_area_profile_mvp') }}

),

bounds as (

    select
        quantile_cont(affordability_ratio, 0.02) as aff_lo,
        median(affordability_ratio) as aff_md,
        quantile_cont(affordability_ratio, 0.98) as aff_hi,
        quantile_cont(crime_rate_per_1000, 0.02) as cr_lo,
        median(crime_rate_per_1000) as cr_md,
        quantile_cont(crime_rate_per_1000, 0.98) as cr_hi,
        quantile_cont(nearest_station_km, 0.02) as st_lo,
        median(nearest_station_km) as st_md,
        quantile_cont(nearest_station_km, 0.98) as st_hi
    from profile

),

scored as (

    select
        p.area_id,
        p.area_name,
        p.local_authority_name,
        p.region,
        -- affordability: lower rent-to-income ratio is better
        round(greatest(0, least(100,
            100.0 - {{ median_anchored('p.affordability_ratio', 'b.aff_lo', 'b.aff_md', 'b.aff_hi') }}
        )), 1) as affordability_score,
        -- safety: lower recorded-crime rate is better (heavy tail → winsorised)
        round(greatest(0, least(100,
            100.0 - {{ median_anchored('p.crime_rate_per_1000', 'b.cr_lo', 'b.cr_md', 'b.cr_hi') }}
        )), 1) as safety_score,
        -- energy: absolute EPC band anchor (D = 50 = typical)
        case p.epc_median_rating
            when 'A' then 100.0 when 'B' then 83.0 when 'C' then 67.0
            when 'D' then 50.0 when 'E' then 33.0 when 'F' then 17.0 when 'G' then 0.0
        end as energy_score,
        -- flood: absolute, 100 - share of postcodes in a flood zone
        case when p.flood_postcode_pct is not null
            then round(greatest(0, least(100, 100.0 - p.flood_postcode_pct)), 1)
        end as flood_score,
        -- convenience: walkable essentials (count/5) blended with station proximity
        case
            when p.walkable_amenity_count is null then null
            when p.nearest_station_km is not null then round(greatest(0, least(100, (
                (100.0 * p.walkable_amenity_count / 5.0)
                + greatest(0, least(100,
                    100.0 - {{ median_anchored('p.nearest_station_km', 'b.st_lo', 'b.st_md', 'b.st_hi') }}
                ))
            ) / 2.0)), 1)
            else round(greatest(0, least(100, 100.0 * p.walkable_amenity_count / 5.0)), 1)
        end as convenience_score
    from profile as p
    cross join bounds as b

),

assembled as (

    select
        *,
        (case when affordability_score is not null then 1 else 0 end)
        + (case when safety_score is not null then 1 else 0 end)
        + (case when energy_score is not null then 1 else 0 end)
        + (case when flood_score is not null then 1 else 0 end)
        + (case when convenience_score is not null then 1 else 0 end)
            as components_available,
        -- weighted geometric mean of available components, floored at 1
        round(exp(
            (
                coalesce({{ var('score_weight_affordability') }} * ln(greatest(affordability_score, 1)), 0)
                + coalesce({{ var('score_weight_safety') }} * ln(greatest(safety_score, 1)), 0)
                + coalesce({{ var('score_weight_energy') }} * ln(greatest(energy_score, 1)), 0)
                + coalesce({{ var('score_weight_flood') }} * ln(greatest(flood_score, 1)), 0)
                + coalesce({{ var('score_weight_convenience') }} * ln(greatest(convenience_score, 1)), 0)
            ) / nullif(
                (case when affordability_score is not null then {{ var('score_weight_affordability') }} else 0 end)
                + (case when safety_score is not null then {{ var('score_weight_safety') }} else 0 end)
                + (case when energy_score is not null then {{ var('score_weight_energy') }} else 0 end)
                + (case when flood_score is not null then {{ var('score_weight_flood') }} else 0 end)
                + (case when convenience_score is not null then {{ var('score_weight_convenience') }} else 0 end),
                0
            )
        ), 1) as overall_score
    from scored

)

select
    area_id,
    area_name,
    local_authority_name,
    region,
    affordability_score,
    safety_score,
    energy_score,
    flood_score,
    convenience_score,
    overall_score,
    dense_rank() over (order by overall_score desc nulls last) as overall_rank,
    components_available,
    case
        when components_available >= 5 then 'high'
        when components_available >= 3 then 'medium'
        else 'low'
    end as confidence_level,
    concat(
        'Strongest on ',
        case greatest(
            affordability_score, safety_score, energy_score, flood_score, convenience_score
        )
            when affordability_score then 'affordability'
            when safety_score then 'safety'
            when energy_score then 'energy efficiency'
            when flood_score then 'low flood risk'
            else 'convenience'
        end,
        ', weakest on ',
        case least(
            affordability_score, safety_score, energy_score, flood_score, convenience_score
        )
            when affordability_score then 'affordability'
            when safety_score then 'safety'
            when energy_score then 'energy efficiency'
            when flood_score then 'flood risk'
            else 'convenience'
        end,
        '. Overall combines ',
        components_available,
        ' of 5 indicators.'
    ) as why_this_area
from assembled
order by overall_score desc nulls last
