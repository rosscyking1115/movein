{{
    config(
        materialized='table'
    )
}}

-- First decision-support mart.
-- Grain: one row per MSOA area_id.
--
-- This profile exposes Land Registry sale context and ONS local-authority
-- rent (with an affordability ratio), plus null/caveated placeholders for the
-- public-data layers still to come. That keeps the product honest: no crime,
-- EPC, flood, planning, or commute claims are made before those sources exist.

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
    cast(null as varchar) as epc_median_rating,
    cast(null as numeric) as crime_rate_per_1000,
    'unknown' as flood_risk_flag,
    0 as planning_constraint_count,
    cast(null as numeric) as commute_minutes_sample,
    'low' as confidence_level,
    case
        when rent.rent_monthly_gbp is not null
            then concat(
                'Land Registry sale context and ONS ',
                rent.rent_grain,
                ' rent loaded; EPC, crime, flood, planning, and commute not loaded yet.'
            )
        else concat(
            'Land Registry sale context loaded; no ONS rent matched for this ',
            'area; EPC, crime, flood, planning, and commute not loaded yet.'
        )
    end as confidence_notes,
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
order by area.region, area.local_authority_name, area.area_name
