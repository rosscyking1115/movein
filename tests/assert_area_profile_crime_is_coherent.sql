-- Risk: a crime rate could appear for an area with no matched crimes, or
--       crimes could aggregate without producing a rate, making the recorded-crime
--       indicator misleading.
--
-- Fail rows: any area where the crime rate and record count disagree, or the
-- rate is negative.

select
    area_id,
    crime_rate_per_1000,
    crime_record_count
from {{ ref('rpt_area_profile_mvp') }}
where
    (crime_rate_per_1000 is not null and coalesce(crime_record_count, 0) = 0)
    or (crime_record_count > 0 and crime_rate_per_1000 is null)
    or (crime_rate_per_1000 < 0)
