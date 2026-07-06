-- EPC energy profile per MSOA: certificate count and median current-efficiency
-- score. rpt_area_profile_mvp bands the median efficiency into an A–G rating.
select
    dpg.area_id,
    count(*) as epc_certificate_count,
    median(epc.current_energy_efficiency) as epc_median_efficiency
from {{ ref('stg_epc__certificates') }} as epc
inner join {{ ref('dim_postcode_geography') }} as dpg
    on epc.postcode = dpg.postcode
where dpg.area_id is not null
group by dpg.area_id
