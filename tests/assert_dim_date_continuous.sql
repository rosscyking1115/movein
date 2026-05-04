-- Risk: dim_date is the calendar spine; if the macro generated a gap,
--       date-spine joins on transferred_on would silently lose rows.
--
-- Fail rows: any pair of consecutive dim_date entries more than 1 day apart.

with ordered as (
    select
        date_day,
        lag(date_day) over (order by date_day) as prev_day
    from {{ ref('dim_date') }}
)

select
    date_day,
    prev_day,
    (date_day - prev_day) as gap_days
from ordered
where prev_day is not null
  and (date_day - prev_day) <> 1
