-- Risk: dense_rank should put at least one area at rank=1 per year. Zero
--       rank=1 rows would mean the rank function silently failed.
--       (Multiple rank=1 rows = ties, which is acceptable.)
--
-- Fail rows: any year with no rank=1 entry.

with per_year as (
    select
        transferred_year,
        count(*) filter (where rank_within_year = 1) as rank_one_count
    from {{ ref('rpt_top_postcodes_by_volume') }}
    group by transferred_year
)

select * from per_year where rank_one_count < 1
