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
    -- Keep only England & Wales MSOA codes (E02/W02). Land Registry covers
    -- England & Wales, so Scottish Intermediate Zones (S02), NI geography, and
    -- ONS pseudo-codes (e.g. L99999999) are treated as "no MSOA" rather than
    -- masquerading as recommendable neighbourhoods.
    case
        when
            nullif(trim(area_id), '') like 'E02%'
            or nullif(trim(area_id), '') like 'W02%'
            then nullif(trim(area_id), '')
    end as area_id,
    nullif(trim(area_name), '') as area_name,
    nullif(trim(lsoa_code), '') as lsoa_code,
    nullif(trim(local_authority_code), '') as local_authority_code,
    nullif(trim(local_authority_name), '') as local_authority_name,
    coalesce(nullif(trim(region), ''), 'Unknown') as region,
    -- ONSPD stores a no-grid-reference sentinel (lat 99.999999) for postcodes
    -- with no centroid. Null both coordinates together so downstream distance
    -- logic never treats the sentinel as a real location.
    case
        when
            cast(latitude as double) between -90 and 90
            and cast(longitude as double) between -180 and 180
            then cast(latitude as double)
    end as latitude,
    case
        when
            cast(latitude as double) between -90 and 90
            and cast(longitude as double) between -180 and 180
            then cast(longitude as double)
    end as longitude,
    cast(is_current_postcode as boolean) as is_current_postcode,
    cast(source_snapshot_date as date) as source_snapshot_date,
    nullif(trim(source_name), '') as source_name,
    nullif(trim(source_url), '') as source_url
{% if var('geo_source') == 'onspd' %}
from {{ source('geo', 'onspd_postcodes') }}
{% else %}
from {{ ref('ref_onspd_sample') }}
{% endif %}
