{{
    config(
        materialized='table'
    )
}}

-- dim_tenure — Land Registry's 3 tenure codes decoded.

select * from (
    values
        ('F', 'Freehold'),
        ('L', 'Leasehold'),
        ('U', 'Unknown')
) as t(tenure_code, tenure_label)
