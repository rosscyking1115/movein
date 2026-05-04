{{
    config(
        materialized='table'
    )
}}

-- dim_property_type — Land Registry's 5 property-type codes decoded.
-- Hand-built rather than seeded because it's tiny, never changes, and
-- inlining the mapping here keeps the dictionary co-located with the dim.

select * from (
    values
        ('D', 'Detached'),
        ('S', 'Semi-detached'),
        ('T', 'Terraced'),
        ('F', 'Flat / Maisonette'),
        ('O', 'Other')
) as t(property_type_code, property_type_label)
