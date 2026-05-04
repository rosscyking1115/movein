-- Risk: same as dim_property_type — static lookup integrity.
--
-- Fail rows: any expected code missing from the dim.

with expected as (
    select unnest(['F', 'L', 'U']) as tenure_code
),

missing as (
    select e.tenure_code
    from expected e
    left join {{ ref('dim_tenure') }} d using (tenure_code)
    where d.tenure_code is null
)

select * from missing
