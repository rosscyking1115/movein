{{
    config(
        materialized='table'
    )
}}

-- rpt_price_yoy_by_region — answers the question:
--     "Where in England + Wales has housing got more or less affordable
--      year-on-year, and how does the regional gap evolve?"
--
-- GRAIN: one row per (region, transferred_year).
--
-- Measures:
--   sales_count           — number of arm's-length sales that year
--   mean_price_gbp        — arithmetic mean (sensitive to high-value tail)
--   median_price_gbp      — robust middle (the metric most analysts cite)
--   p10_price_gbp / p90   — 10th / 90th percentile bookends
--   prior_year_median     — same region, year-1 (LAG)
--   median_yoy_pct        — % change in median vs. prior year
--   mean_yoy_pct          — % change in mean vs. prior year
--
-- 'Unknown' region rows are excluded — they're <0.1% of volume and would
-- pollute the regional ranking. They remain visible in fct_transactions
-- for completeness.

with by_region_year as (

    select
        region,
        transferred_year,
        count(*) as sales_count,
        avg(price_gbp)::bigint as mean_price_gbp,
        (median(price_gbp))::bigint as median_price_gbp,
        (quantile_cont(price_gbp, 0.10))::bigint as p10_price_gbp,
        (quantile_cont(price_gbp, 0.90))::bigint as p90_price_gbp
    from {{ ref('fct_transactions') }}
    where region <> 'Unknown'
    group by region, transferred_year

),

with_prior_year as (

    select
        *,
        lag(median_price_gbp) over (
            partition by region order by transferred_year
        ) as prior_year_median_price_gbp,
        lag(mean_price_gbp) over (
            partition by region order by transferred_year
        ) as prior_year_mean_price_gbp
    from by_region_year

)

select
    region,
    transferred_year,
    sales_count,
    mean_price_gbp,
    median_price_gbp,
    p10_price_gbp,
    p90_price_gbp,
    prior_year_median_price_gbp,
    prior_year_mean_price_gbp,

    -- YoY change rounded to 1 decimal place
    case
        when prior_year_median_price_gbp is null then null
        else round(
            100.0
            * (median_price_gbp - prior_year_median_price_gbp)
            / prior_year_median_price_gbp,
            1
        )
    end as median_yoy_pct,

    case
        when prior_year_mean_price_gbp is null then null
        else round(
            100.0
            * (mean_price_gbp - prior_year_mean_price_gbp)
            / prior_year_mean_price_gbp,
            1
        )
    end as mean_yoy_pct

from with_prior_year
order by region, transferred_year
