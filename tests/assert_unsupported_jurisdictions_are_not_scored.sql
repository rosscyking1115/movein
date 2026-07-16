-- England-only planning and flood sources must never turn absent Welsh
-- coverage into favourable zero facts or a flood-resilience score.

select
    profile.area_id,
    profile.planning_source_status,
    profile.flood_source_status,
    profile.planning_constraint_count,
    profile.flood_postcode_pct,
    profile.flood_risk_flag,
    score.flood_score
from {{ ref('rpt_area_profile_mvp') }} as profile
join {{ ref('rpt_neighbourhood_score') }} as score using (area_id)
where profile.area_id like 'W%'
  and (
      profile.planning_source_status != 'not_covered'
      or profile.flood_source_status != 'not_covered'
      or profile.planning_constraint_count is not null
      or profile.flood_postcode_pct is not null
      or profile.flood_risk_flag is not null
      or score.flood_score is not null
  )
