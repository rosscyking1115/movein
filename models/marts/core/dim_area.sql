{{
    config(
        materialized='table'
    )
}}

-- Canonical decision-support area dimension.
-- MVP grain: one row per MSOA area_id supplied by the postcode lookup.
-- Raw ONS codes (MSOA, local authority, region/country) are resolved to
-- readable names via the committed name seeds. coalesce keeps any name the
-- lookup already supplied (e.g. the fixture), so both build modes stay legible.

with areas as (

    select
        area_id,
        max(area_name) as area_name,
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

)

select
    areas.area_id,
    coalesce(msoa.area_name, areas.area_name) as area_name,
    'MSOA' as area_type,
    areas.local_authority_code,
    coalesce(lad.local_authority_name, areas.local_authority_name)
        as local_authority_name,
    coalesce(rgn.region_name, areas.region) as region,
    areas.centroid_latitude,
    areas.centroid_longitude,
    areas.source_snapshot_date,
    areas.source_name,
    areas.source_url
from areas
left join {{ ref('ref_msoa_names') }} as msoa
    on areas.area_id = msoa.area_id
left join {{ ref('ref_lad_names') }} as lad
    on areas.local_authority_code = lad.local_authority_code
left join {{ ref('ref_region_names') }} as rgn
    on areas.region = rgn.region_code
