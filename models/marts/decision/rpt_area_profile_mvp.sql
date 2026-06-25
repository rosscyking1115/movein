{{
    config(
        materialized='table'
    )
}}

-- First decision-support mart.
-- Grain: one row per MSOA area_id.
--
-- This prototype profile intentionally exposes only Land Registry market
-- context plus null/caveated placeholders for the public-data layers that
-- will be added next. That keeps the product honest: no rent, crime, EPC,
-- flood, planning, or commute claims are made before those sources exist.

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
        on dpg.postcode = fct.postcode
    group by dpg.area_id

)

select
    area.area_id,
    area.area_name,
    area.local_authority_name,
    area.region,
    latest_market.median_sale_price_gbp,
    coalesce(latest_market.sales_count_latest_year, 0)
        as sales_count_latest_year,
    cast(null as numeric) as official_rent_monthly_gbp,
    cast(null as varchar) as rent_source_grain,
    cast(null as numeric) as affordability_ratio,
    cast(null as varchar) as epc_median_rating,
    cast(null as numeric) as crime_rate_per_1000,
    'unknown' as flood_risk_flag,
    0 as planning_constraint_count,
    cast(null as numeric) as commute_minutes_sample,
    'low' as confidence_level,
    concat(
        'Prototype profile: Land Registry sale context only; ',
        'rent, EPC, crime, flood, planning, and commute sources not loaded yet.'
    ) as confidence_notes,
    case
        when coalesce(latest_market.sales_count_latest_year, 0) > 0
            then concat(
                area.area_name,
                ' has Land Registry sale context for ',
                {{ var('landreg_end_year') }},
                ', but recommendation scoring is not active yet.'
            )
        else concat(
            area.area_name,
            ' is present in the geography lookup fixture, ',
            'but has no matched latest-year sale context yet.'
        )
    end as why_this_area
from {{ ref('dim_area') }} as area
left join latest_market
    on area.area_id = latest_market.area_id
order by area.region, area.local_authority_name, area.area_name
