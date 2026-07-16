-- Risk: prototype area rows could expose placeholder null source layers
--       without telling users that the recommendation evidence is incomplete.
--
-- Fail rows: any area profile missing notes while any core source layer is
-- still absent.

select
    area_id,
    area_name
from {{ ref('rpt_area_profile_mvp') }}
where
    (
        official_rent_monthly_gbp is null
        or epc_median_rating is null
        or crime_rate_per_1000 is null
        or commute_minutes_sample is null
    )
    and nullif(trim(source_coverage_notes), '') is null
