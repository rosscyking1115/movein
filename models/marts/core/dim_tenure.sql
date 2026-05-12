{{
    config(
        materialized='table'
    )
}}

-- dim_tenure — Land Registry's 3 tenure codes decoded.
-- The `as t (col_a, col_b)` clause names the VALUES table's columns;
-- without it DuckDB falls back to col0/col1 and downstream tests break.

select
    tenure_code,
    tenure_label
from (
    values
    ('F', 'Freehold'),
    ('L', 'Leasehold'),
    ('U', 'Unknown')
) as t (tenure_code, tenure_label)
