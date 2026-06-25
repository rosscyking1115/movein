{{
    config(
        materialized='table'
    )
}}

-- Postcode-to-area bridge for the housing decision-support direction.
-- Grain: one row per normalised postcode in the official lookup snapshot.

select
    postcode,
    postcode_outward,
    postcode_area,
    area_id,
    lsoa_code,
    local_authority_code,
    region,
    latitude,
    longitude,
    is_current_postcode,
    true as is_in_source_lookup,
    source_snapshot_date
from {{ ref('stg_geo__postcodes') }}
