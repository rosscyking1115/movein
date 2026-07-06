-- Police street-crime volume per MSOA, mapped LSOA → area. rpt_area_profile_mvp
-- turns record_count / months_observed / population into an approximate,
-- clearly-caveated crime rate per 1,000 residents.
with lsoa_to_area as (

    select distinct
        lsoa_code,
        area_id
    from {{ ref('dim_postcode_geography') }}
    where area_id is not null and lsoa_code is not null

)

select
    l.area_id,
    count(*) as crime_record_count,
    count(distinct c.crime_month) as crime_months_observed
from {{ ref('stg_crime__street') }} as c
inner join lsoa_to_area as l
    on c.lsoa_code = l.lsoa_code
group by l.area_id
