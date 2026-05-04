{{
    config(
        materialized='table'
    )
}}

-- rpt_top_postcodes_by_volume — answers:
--     "Which postcode areas are the hottest markets each year, and is
--      that ranking shifting?"
--
-- GRAIN: one row per (postcode_area, transferred_year).
--
-- Measures:
--   sales_count        — transaction volume
--   mean_price_gbp     — average sale price for context (a top-volume
--                        area can be cheap-and-busy or expensive-and-busy)
--   rank_within_year   — DENSE_RANK on sales_count desc; 1 = busiest
--                        area in that year
--
-- Dashboard usage: filter to rank_within_year <= 20 for a top-20 view.

with by_area_year as (

    select
        postcode_area,
        region,
        transferred_year,
        count(*)                                                as sales_count,
        avg(price_gbp)::bigint                                  as mean_price_gbp,
        cast(median(price_gbp) as bigint)                       as median_price_gbp
    from {{ ref('fct_transactions') }}
    where postcode_area is not null
    group by postcode_area, region, transferred_year

)

select
    postcode_area,
    region,
    transferred_year,
    sales_count,
    mean_price_gbp,
    median_price_gbp,
    dense_rank() over (
        partition by transferred_year
        order by sales_count desc
    )                                                           as rank_within_year
from by_area_year
order by transferred_year, rank_within_year
