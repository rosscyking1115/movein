{{
    config(
        materialized='table'
    )
}}

-- First decision-support mart.
-- Grain: one row per MSOA area_id.
--
-- This profile exposes Land Registry sale context, ONS local-authority rent
-- (with an affordability ratio), an EPC energy-efficiency profile, a police
-- street-crime indicator, planning-constraint / flood-risk flags, and
-- OpenStreetMap amenity/convenience access, plus a null placeholder for
-- door-to-door commute time. That keeps the product honest: no journey-time
-- commute claims are made before that source exists.
--
-- The per-source area aggregations live in the intermediate layer
-- (int_area__market / __energy / __crime / __nearest_city); this mart assembles
-- them onto the dim_area spine and derives the presentation columns (EPC band,
-- affordability ratio, crime rate, confidence notes, "why this area").

select
    area.area_id,
    area.area_name,
    area.local_authority_name,
    area.region,
    latest_market.median_sale_price_gbp,
    coalesce(latest_market.sales_count_latest_year, 0)
        as sales_count_latest_year,
    -- Sample-depth confidence for the median: a median over a handful of
    -- transactions is an outlier magnet (prime-central areas can show a £13M
    -- median from 2 sales). Flag it instead of presenting it as fact.
    case
        when coalesce(latest_market.sales_count_latest_year, 0) = 0 then 'none'
        when
            latest_market.sales_count_latest_year
            < {{ var('min_reliable_sale_sample') }} then 'indicative'
        else 'reliable'
    end as median_sale_price_confidence,
    rent.rent_monthly_gbp as official_rent_monthly_gbp,
    rent.rent_grain as rent_source_grain,
    round(
        rent.rent_monthly_gbp / {{ var('default_monthly_net_income_gbp') }}, 3
    ) as affordability_ratio,
    rent.rent_1bed_gbp,
    rent.rent_2bed_gbp,
    rent.rent_3bed_gbp,
    rent.rent_4plus_gbp,
    case
        when area_energy.epc_median_efficiency >= 92 then 'A'
        when area_energy.epc_median_efficiency >= 81 then 'B'
        when area_energy.epc_median_efficiency >= 69 then 'C'
        when area_energy.epc_median_efficiency >= 55 then 'D'
        when area_energy.epc_median_efficiency >= 39 then 'E'
        when area_energy.epc_median_efficiency >= 21 then 'F'
        when area_energy.epc_median_efficiency >= 1 then 'G'
    end as epc_median_rating,
    area_energy.epc_certificate_count,
    round(
        (area_crime.crime_record_count / area_crime.crime_months_observed)
        / {{ var('nominal_msoa_population') }} * 1000,
        2
    ) as crime_rate_per_1000,
    area_crime.crime_record_count,
    coalesce(cons.flood_risk_flag, 'unknown') as flood_risk_flag,
    cons.flood_postcode_pct,
    coalesce(cons.planning_constraint_count, 0)
        as planning_constraint_count,
    amenity.nearest_station_km,
    amenity.nearest_supermarket_km,
    amenity.nearest_gp_km,
    amenity.nearest_school_km,
    amenity.nearest_greenspace_km,
    amenity.walkable_amenity_count,
    cen.latitude,
    cen.longitude,
    near.nearest_city,
    near.distance_to_city_km,
    cast(null as numeric) as commute_minutes_sample,
    'low' as confidence_level,
    concat(
        'Loaded: Land Registry sales',
        case when rent.rent_monthly_gbp is not null then ', ONS rent' else '' end,
        case
            when area_energy.epc_certificate_count is not null
                then ', EPC energy'
            else ''
        end,
        case
            when area_crime.crime_record_count is not null
                then ', police crime'
            else ''
        end,
        case
            when cons.area_id is not null
                then ', planning/flood constraints'
            else ''
        end,
        case
            when amenity.area_id is not null
                then ', amenity access'
            else ''
        end,
        '. Not yet loaded: door-to-door commute time.'
    ) as confidence_notes,
    case
        when coalesce(latest_market.sales_count_latest_year, 0) = 0
            then concat(
                area.area_name,
                ' is present in the geography lookup fixture, ',
                'but has no matched latest-year sale context yet.'
            )
        when
            latest_market.sales_count_latest_year
            < {{ var('min_reliable_sale_sample') }}
            then concat(
                area.area_name,
                ' has only ',
                latest_market.sales_count_latest_year,
                ' matched ',
                {{ var('landreg_end_year') }},
                ' sales, so its median is indicative only; ',
                'recommendation scoring is not active yet.'
            )
        else concat(
            area.area_name,
            ' has ',
            latest_market.sales_count_latest_year,
            ' matched ',
            {{ var('landreg_end_year') }},
            ' sales of Land Registry context, ',
            'but recommendation scoring is not active yet.'
        )
    end as why_this_area
from {{ ref('dim_area') }} as area
left join {{ ref('int_area__market') }} as latest_market
    on area.area_id = latest_market.area_id
left join {{ ref('ref_ons_rent') }} as rent
    on area.local_authority_code = rent.area_code
left join {{ ref('int_area__energy') }} as area_energy
    on area.area_id = area_energy.area_id
left join {{ ref('int_area__crime') }} as area_crime
    on area.area_id = area_crime.area_id
left join {{ ref('stg_constraints__area') }} as cons
    on area.area_id = cons.area_id
left join {{ ref('stg_amenities__area') }} as amenity
    on area.area_id = amenity.area_id
left join {{ ref('ref_msoa_centroid') }} as cen
    on area.area_id = cen.area_id
left join {{ ref('int_area__nearest_city') }} as near
    on area.area_id = near.area_id
order by area.region, area.local_authority_name, area.area_name
