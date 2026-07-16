{{
    config(
        materialized='view'
    )
}}

-- Street-level crime staging interface for the recorded-crime indicator.
-- Reads the committed ref_crime_sample fixture by default, or the full
-- raw_police.street_crime source when built with `--vars 'crime_source: bulk'`.
-- Grain: one row per recorded crime. Keyed by 2021 LSOA, which rolls up to MSOA.

select
    upper(trim(lsoa_code)) as lsoa_code,
    nullif(trim(crime_type), '') as crime_type,
    nullif(trim(cast(month as varchar)), '') as crime_month
{% if var('crime_source') == 'bulk' %}
from {{ source('police', 'street_crime') }}
{% else %}
from {{ ref('ref_crime_sample') }}
{% endif %}
where nullif(trim(lsoa_code), '') is not null
