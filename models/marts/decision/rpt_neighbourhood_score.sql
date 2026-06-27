{{
    config(
        materialized='table'
    )
}}

-- Phase 4: explainable neighbourhood scoring.
--
-- Each component is a 0-100 percentile score across all areas (higher = better),
-- derived from the raw rpt_area_profile_mvp facts. The overall_score is a
-- weighted average of the components an area actually has (default weights from
-- vars); the app re-weights per user from these stored component scores without
-- changing them. A missing component lowers confidence and is dropped from the
-- average rather than scored zero, so absent data never looks like a bad result.

with profile as (

    select * from {{ ref('rpt_area_profile_mvp') }}

),

scored as (

    select
        area_id,
        area_name,
        local_authority_name,
        region,
        -- affordability: a lower rent-to-income ratio is better
        case
            when affordability_ratio is not null
                then round(100 * percent_rank() over (
                    order by affordability_ratio desc nulls last
                ), 1)
        end as affordability_score,
        -- safety: a lower recorded-crime rate is better
        case
            when crime_rate_per_1000 is not null
                then round(100 * percent_rank() over (
                    order by crime_rate_per_1000 desc nulls last
                ), 1)
        end as safety_score,
        -- energy: a higher EPC band is better
        case
            when epc_median_rating is not null
                then round(100 * percent_rank() over (
                    order by case epc_median_rating
                        when 'A' then 7
                        when 'B' then 6
                        when 'C' then 5
                        when 'D' then 4
                        when 'E' then 3
                        when 'F' then 2
                        when 'G' then 1
                    end asc nulls last
                ), 1)
        end as energy_score,
        -- flood: a smaller share of postcodes in a flood zone is better
        case
            when flood_postcode_pct is not null
                then round(100 * percent_rank() over (
                    order by flood_postcode_pct desc nulls last
                ), 1)
        end as flood_score,
        -- convenience: more walkable essentials and a closer station are better.
        -- Walkable count is always present; station proximity falls back to the
        -- walkable score when no station is within range (rural areas are not
        -- penalised to zero on a single missing station).
        round((
            100 * percent_rank() over (order by walkable_amenity_count asc nulls last)
            + coalesce(
                case
                    when nearest_station_km is not null
                        then 100 * percent_rank() over (
                            order by nearest_station_km desc nulls last
                        )
                end,
                100 * percent_rank() over (order by walkable_amenity_count asc nulls last)
            )
        ) / 2, 1) as convenience_score
    from profile

),

assembled as (

    select
        *,
        round(
            (
                coalesce({{ var('score_weight_affordability') }} * affordability_score, 0)
                + coalesce({{ var('score_weight_safety') }} * safety_score, 0)
                + coalesce({{ var('score_weight_energy') }} * energy_score, 0)
                + coalesce({{ var('score_weight_flood') }} * flood_score, 0)
                + coalesce({{ var('score_weight_convenience') }} * convenience_score, 0)
            ) / nullif(
                (case
                    when affordability_score is not null
                        then {{ var('score_weight_affordability') }}
                    else 0
                end)
                + (case
                    when safety_score is not null
                        then {{ var('score_weight_safety') }}
                    else 0
                end)
                + (case
                    when energy_score is not null
                        then {{ var('score_weight_energy') }}
                    else 0
                end)
                + (case
                    when flood_score is not null
                        then {{ var('score_weight_flood') }}
                    else 0
                end)
                + (case
                    when convenience_score is not null
                        then {{ var('score_weight_convenience') }}
                    else 0
                end),
                0
            ),
            1
        ) as overall_score,
        (case when affordability_score is not null then 1 else 0 end)
        + (case when safety_score is not null then 1 else 0 end)
        + (case when energy_score is not null then 1 else 0 end)
        + (case when flood_score is not null then 1 else 0 end)
        + (case when convenience_score is not null then 1 else 0 end)
            as components_available
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
            affordability_score, safety_score, energy_score,
            flood_score, convenience_score
        )
            when affordability_score then 'affordability'
            when safety_score then 'safety'
            when energy_score then 'energy efficiency'
            when flood_score then 'low flood risk'
            else 'convenience'
        end,
        ', weakest on ',
        case least(
            affordability_score, safety_score, energy_score,
            flood_score, convenience_score
        )
            when affordability_score then 'affordability'
            when safety_score then 'safety'
            when energy_score then 'energy efficiency'
            when flood_score then 'flood risk'
            else 'convenience'
        end,
        '. Overall score combines ',
        components_available,
        ' of 5 components.'
    ) as why_this_area
from assembled
order by overall_score desc nulls last
