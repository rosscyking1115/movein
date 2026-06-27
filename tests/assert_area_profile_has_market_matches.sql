-- Risk: the fixture-backed area profile could compile while never exercising
--       a real Land Registry-to-geography join.
--
-- Fail rows: one row if no area has a matched latest-year sale count.

select 1 as no_market_matches
where not exists (
    select 1
    from {{ ref('rpt_area_profile_mvp') }}
    where sales_count_latest_year > 0
)
