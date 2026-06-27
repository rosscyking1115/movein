{{
    config(
        materialized='view'
    )
}}

-- Domestic EPC certificate staging interface for the energy profile layer.
-- Reads the committed ref_epc_sample fixture by default, or the full
-- raw_epc.certificates source when built with `--vars 'epc_source: bulk'`.
-- Grain: one row per certificate.

select
    upper(trim(postcode)) as postcode,
    upper(trim(current_energy_rating)) as current_energy_rating,
    cast(current_energy_efficiency as integer) as current_energy_efficiency,
    nullif(trim(property_type), '') as property_type,
    cast(lodgement_date as date) as lodgement_date
{% if var('epc_source') == 'bulk' %}
from {{ source('epc', 'certificates') }}
{% else %}
from {{ ref('ref_epc_sample') }}
{% endif %}
where
    nullif(trim(current_energy_rating), '') is not null
    and try_cast(current_energy_efficiency as integer) between 1 and 100
