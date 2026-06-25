{{
    config(
        materialized='view'
    )
}}

-- ONSPD-shaped postcode geography staging fixture.
--
-- This is the contract-proving slice for the housing decision-support
-- geography layer. The full official ONSPD snapshot should land behind this
-- same column interface once the model and tests are stable.

select
    upper(trim(postcode)) as postcode,
    upper(trim(postcode_outward)) as postcode_outward,
    upper(trim(postcode_area)) as postcode_area,
    nullif(trim(area_id), '') as area_id,
    nullif(trim(area_name), '') as area_name,
    nullif(trim(lsoa_code), '') as lsoa_code,
    nullif(trim(local_authority_code), '') as local_authority_code,
    nullif(trim(local_authority_name), '') as local_authority_name,
    coalesce(nullif(trim(region), ''), 'Unknown') as region,
    cast(latitude as double) as latitude,
    cast(longitude as double) as longitude,
    cast(is_current_postcode as boolean) as is_current_postcode,
    cast(source_snapshot_date as date) as source_snapshot_date,
    nullif(trim(source_name), '') as source_name,
    nullif(trim(source_url), '') as source_url
from {{ ref('ref_onspd_sample') }}
