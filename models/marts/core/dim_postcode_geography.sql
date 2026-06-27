{{
    config(
        materialized='table'
    )
}}

-- Postcode-to-area bridge for the housing decision-support direction.
-- Grain: one row per normalised postcode in the official lookup snapshot.

select
    geo.postcode,
    geo.postcode_outward,
    geo.postcode_area,
    geo.area_id,
    geo.lsoa_code,
    geo.local_authority_code,
    coalesce(rgn.region_name, geo.region) as region,
    geo.latitude,
    geo.longitude,
    geo.is_current_postcode,
    true as is_in_source_lookup,
    geo.source_snapshot_date
from {{ ref('stg_geo__postcodes') }} as geo
left join {{ ref('ref_region_names') }} as rgn
    on geo.region = rgn.region_code
