{{
    config(
        materialized='table'
    )
}}

-- Canonical decision-support area dimension.
-- MVP grain: one row per MSOA-like area_id supplied by the postcode lookup.

select
    area_id,
    max(area_name) as area_name,
    'MSOA' as area_type,
    max(local_authority_code) as local_authority_code,
    max(local_authority_name) as local_authority_name,
    max(region) as region,
    avg(latitude) as centroid_latitude,
    avg(longitude) as centroid_longitude,
    max(source_snapshot_date) as source_snapshot_date,
    max(source_name) as source_name,
    max(source_url) as source_url
from {{ ref('stg_geo__postcodes') }}
where area_id is not null
group by area_id
