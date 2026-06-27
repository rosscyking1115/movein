-- Risk: an EPC median band could appear for an area with no certificates, or
--       certificates could aggregate without producing a band — either of which
--       would make the energy signal misleading.
--
-- Fail rows: any area where the EPC band and certificate count disagree.

select
    area_id,
    epc_median_rating,
    epc_certificate_count
from {{ ref('rpt_area_profile_mvp') }}
where
    (epc_median_rating is not null and coalesce(epc_certificate_count, 0) = 0)
    or (epc_certificate_count > 0 and epc_median_rating is null)
