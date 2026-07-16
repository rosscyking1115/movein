-- A component must be null when the fact required to calculate it is absent.
-- This guards DuckDB's least/greatest null behaviour from manufacturing a
-- favourable endpoint score around an otherwise null calculation.

select
    profile.area_id,
    score.affordability_score,
    score.safety_score,
    score.energy_score,
    score.flood_score,
    score.convenience_score
from {{ ref('rpt_area_profile_mvp') }} as profile
join {{ ref('rpt_neighbourhood_score') }} as score using (area_id)
where (profile.affordability_ratio is null and score.affordability_score is not null)
   or (profile.crime_rate_per_1000 is null and score.safety_score is not null)
   or (profile.epc_median_rating is null and score.energy_score is not null)
   or (profile.flood_postcode_pct is null and score.flood_score is not null)
   or (profile.walkable_amenity_count is null and score.convenience_score is not null)
