{{
    config(
        materialized='view'
    )
}}

-- Per-MSOA amenity/convenience access staging interface.
-- Reads the committed ref_amenity_access_sample fixture by default, or the
-- OpenStreetMap-derived raw_amenities.area_access source when built with
-- `--vars 'amenities_source: computed'`. Grain: one row per area_id.
-- Distances are km from the MSOA centroid to the nearest amenity of each type
-- (null when none is within the search cap).

select
    area_id,
    cast(nearest_station_km as double) as nearest_station_km,
    cast(nearest_supermarket_km as double) as nearest_supermarket_km,
    cast(nearest_gp_km as double) as nearest_gp_km,
    cast(nearest_school_km as double) as nearest_school_km,
    cast(nearest_greenspace_km as double) as nearest_greenspace_km,
    cast(walkable_amenity_count as integer) as walkable_amenity_count
{% if var('amenities_source') == 'computed' %}
from {{ source('amenities', 'area_access') }}
{% else %}
from {{ ref('ref_amenity_access_sample') }}
{% endif %}
