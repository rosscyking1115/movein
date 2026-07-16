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
-- evidence quality and is dropped, never scored zero.
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
        p.rent_source_grain,
        p.rent_reference_date,
        p.median_sale_price_confidence,
        p.crime_population_denominator,
        p.crime_population_reference_date,
        p.crime_period_start,
        p.crime_period_end,
        p.planning_source_status,
        p.flood_source_status,
        -- Strong evidence stays unavailable until the public extract carries
        -- dated provenance for every scored component (including EPC, flood,
        -- and amenities), rather than inferring dates that are not present.
        false as all_component_source_dates_known,
        -- affordability: lower rent-to-income ratio is better
        case when p.affordability_ratio is not null then
            round(greatest(0, least(100,
                100.0 - {{ median_anchored('p.affordability_ratio', 'b.aff_lo', 'b.aff_md', 'b.aff_hi') }}
            )), 1)
        end as affordability_score,
        -- recorded crime: lower rate is better (heavy tail → winsorised)
        case when p.crime_rate_per_1000 is not null then
            round(greatest(0, least(100,
                100.0 - {{ median_anchored('p.crime_rate_per_1000', 'b.cr_lo', 'b.cr_md', 'b.cr_hi') }}
            )), 1)
        end as safety_score,
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
                coalesce({{ validated_score_weight('affordability') }} * ln(greatest(affordability_score, 1)), 0)
                + coalesce({{ validated_score_weight('safety') }} * ln(greatest(safety_score, 1)), 0)
                + coalesce({{ validated_score_weight('energy') }} * ln(greatest(energy_score, 1)), 0)
                + coalesce({{ validated_score_weight('flood') }} * ln(greatest(flood_score, 1)), 0)
                + coalesce({{ validated_score_weight('convenience') }} * ln(greatest(convenience_score, 1)), 0)
            ) / nullif(
                (case when affordability_score is not null then {{ validated_score_weight('affordability') }} else 0 end)
                + (case when safety_score is not null then {{ validated_score_weight('safety') }} else 0 end)
                + (case when energy_score is not null then {{ validated_score_weight('energy') }} else 0 end)
                + (case when flood_score is not null then {{ validated_score_weight('flood') }} else 0 end)
                + (case when convenience_score is not null then {{ validated_score_weight('convenience') }} else 0 end),
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
    components_available as available_component_count,
    5 as expected_component_count,
    all_component_source_dates_known,
    case
        when components_available < 3
            or crime_population_denominator is null
            or flood_source_status is distinct from 'covered'
            or planning_source_status is distinct from 'covered'
            then 'limited'
        when components_available = 5
            and rent_source_grain = 'msoa'
            and median_sale_price_confidence = 'reliable'
            and all_component_source_dates_known
            and rent_reference_date is not null
            and crime_population_reference_date is not null
            and crime_period_start is not null
            and crime_period_end is not null
            then 'strong'
        else 'mixed'
    end as evidence_quality_level,
    case
        when components_available < 3 then concat(
            'Limited evidence: only ', components_available, ' of 5 scored indicators are available.'
        )
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
    concat(
        'Strongest on ',
        case greatest(
            affordability_score, safety_score, energy_score, flood_score, convenience_score
        )
            when affordability_score then 'affordability'
            when safety_score then 'recorded crime'
            when energy_score then 'energy efficiency'
            when flood_score then 'low flood risk'
            else 'convenience'
        end,
        ', weakest on ',
        case least(
            affordability_score, safety_score, energy_score, flood_score, convenience_score
        )
            when affordability_score then 'affordability'
            when safety_score then 'recorded crime'
            when energy_score then 'energy efficiency'
            when flood_score then 'flood risk'
            else 'convenience'
        end,
        '. Overall combines ',
        components_available,
        ' of 5 indicators.'
    ) as why_this_area
from assembled
order by overall_score desc nulls last, area_id asc
