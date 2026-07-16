-- Fail any scored crime rate without its compatible, dated MSOA denominator,
-- or when the published rate does not reproduce from the exposed evidence.

select
    area_id,
    crime_rate_per_1000,
    crime_record_count,
    crime_months_observed,
    crime_population_denominator
from {{ ref('rpt_area_profile_mvp') }}
where crime_rate_per_1000 is not null
  and (
      crime_population_denominator is null
      or crime_population_reference_date != date '2024-06-30'
      or crime_population_geography != 'MSOA 2021'
      or nullif(trim(crime_population_source_name), '') is null
      or crime_months_observed is null
      or crime_months_observed <= 0
      or abs(
          crime_rate_per_1000
          - round(
              crime_record_count::double
              / crime_months_observed
              / crime_population_denominator
              * 1000,
              2
          )
      ) > 0.001
  )
