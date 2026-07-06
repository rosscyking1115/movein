-- Nearest major city centre to each MSOA centroid (haversine distance), for
-- orientation in the area profile. One row per area_id (the closest city).
select
    area_id,
    nearest_city,
    distance_to_city_km
from (
    select
        cen.area_id,
        cty.city as nearest_city,
        round(
            {{ haversine_km('cen.latitude', 'cen.longitude', 'cty.latitude', 'cty.longitude') }}, 1
        ) as distance_to_city_km,
        row_number() over (
            partition by cen.area_id
            order by {{ haversine_km('cen.latitude', 'cen.longitude', 'cty.latitude', 'cty.longitude') }} asc
        ) as rn
    from {{ ref('ref_msoa_centroid') }} as cen
    cross join {{ ref('ref_city_centre') }} as cty
)
where rn = 1
