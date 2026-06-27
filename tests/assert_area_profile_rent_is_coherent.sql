-- Risk: rent could appear without its source grain or affordability ratio, or
--       as a non-positive value, making the affordability signal misleading or
--       breaking the contract ("rent_source_grain non-null whenever
--       official_rent_monthly_gbp is non-null").
--
-- Fail rows: any area profile where rent, grain, and affordability disagree, or
-- rent is non-positive.

select
    area_id,
    official_rent_monthly_gbp,
    rent_source_grain,
    affordability_ratio
from {{ ref('rpt_area_profile_mvp') }}
where
    (official_rent_monthly_gbp is not null and rent_source_grain is null)
    or (rent_source_grain is not null and official_rent_monthly_gbp is null)
    or (official_rent_monthly_gbp is not null and affordability_ratio is null)
    or (official_rent_monthly_gbp is not null and official_rent_monthly_gbp <= 0)
