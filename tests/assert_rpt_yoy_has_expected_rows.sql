-- Risk: a one-year sample can make YoY tests pass without exercising the
--       LAG calculation at all. This test fails unless the report has at
--       least two years and every non-first year has YoY values.

with summary as (

    select
        count(distinct transferred_year) as year_count,
        min(transferred_year) as first_year
    from {{ ref('rpt_price_yoy_by_region') }}

),

too_few_years as (

    select
        'fewer_than_two_years' as failure_type,
        cast(null as varchar) as region,
        cast(null as integer) as transferred_year,
        cast(null as double) as median_yoy_pct,
        cast(null as double) as mean_yoy_pct
    from summary
    where year_count < 2

),

missing_yoy as (

    select
        'missing_yoy_after_first_year' as failure_type,
        yoy.region,
        yoy.transferred_year,
        yoy.median_yoy_pct,
        yoy.mean_yoy_pct
    from {{ ref('rpt_price_yoy_by_region') }} as yoy
    cross join summary
    where
        yoy.transferred_year > summary.first_year
        and (
            yoy.median_yoy_pct is null
            or yoy.mean_yoy_pct is null
        )

)

select * from too_few_years
union all
select * from missing_yoy
