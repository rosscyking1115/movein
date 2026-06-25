-- Risk: dim_date must cover the configured Land Registry analysis window
--       plus one buffer year on either side. If the spine is too short,
--       relationship tests and future refreshes can fail unexpectedly.
--
-- Fail rows: one row if dim_date starts after the expected buffer start
-- or ends before the expected buffer end.

with bounds as (
    select
        min(date_day) as min_date_day,
        max(date_day) as max_date_day
    from {{ ref('dim_date') }}
),

expected as (
    select
        date '{{ var("landreg_start_year") - 1 }}-01-01' as expected_start,
        date '{{ var("landreg_end_year") + 1 }}-12-31' as expected_end
)

select
    bounds.min_date_day,
    bounds.max_date_day,
    expected.expected_start,
    expected.expected_end
from bounds
cross join expected
where
    bounds.min_date_day > expected.expected_start
    or bounds.max_date_day < expected.expected_end
