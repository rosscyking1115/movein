{{
    config(
        materialized='table'
    )
}}

-- rpt_new_build_premium — answers:
--     "How much extra do you pay for new construction in each region,
--      and is that gap widening, narrowing, or stable?"
--
-- GRAIN: one row per (region, transferred_year).
--
-- Pivots is_new_build into separate columns rather than separate rows,
-- so a single row contains both 'new' and 'existing' aggregates plus
-- the derived premium. This makes dashboard charts trivial to build:
--   premium_pct on the y-axis, transferred_year on the x-axis,
--   one line per region.
--
-- 'Unknown' region rows are excluded for the same reason as in
-- rpt_price_yoy_by_region.

with pivoted as (

    select
        region,
        transferred_year,
        count(*) filter (where is_new_build)                    as new_build_count,
        count(*) filter (where not is_new_build)                as existing_count,
        cast(avg(price_gbp) filter (where is_new_build) as bigint)
                                                                as new_build_mean_price_gbp,
        cast(avg(price_gbp) filter (where not is_new_build) as bigint)
                                                                as existing_mean_price_gbp,
        cast(median(price_gbp) filter (where is_new_build) as bigint)
                                                                as new_build_median_price_gbp,
        cast(median(price_gbp) filter (where not is_new_build) as bigint)
                                                                as existing_median_price_gbp
    from {{ ref('fct_transactions') }}
    where region <> 'Unknown'
    group by region, transferred_year

)

select
    region,
    transferred_year,
    new_build_count,
    existing_count,
    new_build_mean_price_gbp,
    existing_mean_price_gbp,
    new_build_median_price_gbp,
    existing_median_price_gbp,

    -- premium_pct — how much more (positive) or less (negative) a new-build
    -- costs vs. an existing property of unknown type in the same region
    -- and year. Median-based — robust to outliers.
    case
        when existing_median_price_gbp is null
            or existing_median_price_gbp = 0
            or new_build_median_price_gbp is null
        then null
        else round(
            100.0
            * (new_build_median_price_gbp - existing_median_price_gbp)
            / existing_median_price_gbp
        , 1)
    end                                                         as premium_pct

from pivoted
order by region, transferred_year
