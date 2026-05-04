{{
    config(
        materialized='table'
    )
}}

-- dim_postcode — one row per distinct postcode that appears in the
-- transactions data, with three levels of geographic rollup:
--
--   postcode  → 'SW1A 1AA'     (full postcode at time of sale)
--   outward   → 'SW1A'          (district)
--   area      → 'SW'            (broadest geographic group, joins to seed)
--   region    → 'London'        (10 ONS regions of England + Wales)
--
-- Postcodes are NULL in a small number of historic records; we filter
-- those out here so dim_postcode has a clean primary key. The fact table
-- handles the NULL-postcode case via a left-join + 'Unknown' fallback.

with distinct_postcodes as (

    select distinct
        postcode,
        postcode_outward,
        postcode_area,
        region
    from {{ ref('int_transactions__enriched') }}
    where postcode is not null

)

select
    {{ dbt_utils.generate_surrogate_key(['postcode']) }}      as postcode_key,
    postcode,
    postcode_outward,
    postcode_area,
    region
from distinct_postcodes
