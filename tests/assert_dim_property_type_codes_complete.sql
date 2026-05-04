-- Risk: dim_property_type is a static lookup; if a code went missing
--       (e.g. someone deleted a row), fct_transactions joins for that
--       property type would lose label context.
--
-- Fail rows: any expected code missing from the dim.

with expected as (
    select unnest(['D', 'S', 'T', 'F', 'O']) as property_type_code
),

missing as (
    select e.property_type_code
    from expected e
    left join {{ ref('dim_property_type') }} d using (property_type_code)
    where d.property_type_code is null
)

select * from missing
