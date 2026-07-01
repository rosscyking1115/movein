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

with latest_market as (

    select
        dpg.area_id,
        count(fct.transaction_id) filter (
            where fct.transferred_year = {{ var('landreg_end_year') }}
        ) as sales_count_latest_year,
        cast(
            median(fct.price_gbp) filter (
                where fct.transferred_year = {{ var('landreg_end_year') }}
            ) as bigint
        ) as median_sale_price_gbp
    from {{ ref('dim_postcode_geography') }} as dpg
    left join {{ ref('fct_transactions') }} as fct
        on dpg.postcode = upper(trim(fct.postcode))
    group by dpg.area_id

),

area_energy as (

    select
        dpg.area_id,
        count(*) as epc_certificate_count,
        median(epc.current_energy_efficiency) as epc_median_efficiency
    from {{ ref('stg_epc__certificates') }} as epc
    inner join {{ ref('dim_postcode_geography') }} as dpg
        on epc.postcode = dpg.postcode
    where dpg.area_id is not null
    group by dpg.area_id

),

lsoa_to_area as (

    select distinct
        lsoa_code,
        area_id
    from {{ ref('dim_postcode_geography') }}
    where area_id is not null and lsoa_code is not null

),

area_crime as (

    select
        l.area_id,
        count(*) as crime_record_count,
        count(distinct c.crime_month) as crime_months_observed
    from {{ ref('stg_crime__street') }} as c
    inner join lsoa_to_area as l
        on c.lsoa_code = l.lsoa_code
    group by l.area_id

),

nearest_city as (

    select area_id, nearest_city, distance_to_city_km
    from (
        select
            cen.area_id,
            cty.city as nearest_city,
            round({{ haversine_km('cen.latitude', 'cen.longitude', 'cty.latitude', 'cty.longitude') }}, 1)
                as distance_to_city_km,
            row_number() over (
                partition by cen.area_id
                order by {{ haversine_km('cen.latitude', 'cen.longitude', 'cty.latitude', 'cty.longitude') }} asc
            ) as rn
        from {{ ref('ref_msoa_centroid') }} as cen
        cross join {{ ref('ref_city_centre') }} as cty
    )
    where rn = 1

)

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
left join latest_market
    on area.area_id = latest_market.area_id
left join {{ ref('ref_ons_rent') }} as rent
    on area.local_authority_code = rent.area_code
left join area_energy
    on area.area_id = area_energy.area_id
left join area_crime
    on area.area_id = area_crime.area_id
left join {{ ref('stg_constraints__area') }} as cons
    on area.area_id = cons.area_id
left join {{ ref('stg_amenities__area') }} as amenity
    on area.area_id = amenity.area_id
left join {{ ref('ref_msoa_centroid') }} as cen
    on area.area_id = cen.area_id
left join nearest_city as near
    on area.area_id = near.area_id
order by area.region, area.local_authority_name, area.area_name
