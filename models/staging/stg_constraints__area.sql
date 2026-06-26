{{
    config(
        materialized='view'
    )
}}

-- Per-MSOA planning-constraint + flood-risk staging interface.
-- Reads the committed ref_area_constraints_sample fixture by default, or the
-- spatially-computed raw_constraints.area_constraints source when built with
-- `--vars 'constraints_source: computed'`. Grain: one row per area_id.

select
    area_id,
    cast(planning_constraint_count as integer) as planning_constraint_count,
    lower(trim(flood_risk_flag)) as flood_risk_flag,
    cast(flood_postcode_pct as double) as flood_postcode_pct
{% if var('constraints_source') == 'computed' %}
from {{ source('constraints', 'area_constraints') }}
{% else %}
from {{ ref('ref_area_constraints_sample') }}
{% endif %}
