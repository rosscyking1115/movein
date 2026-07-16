{{
    config(
        materialized='view'
    )
}}

-- Per-MSOA planning-constraint + flood-risk staging interface.
-- Reads the committed ref_area_constraints_sample fixture by default, or the
-- spatially-computed raw_constraints.area_constraints source when built with
-- `--vars 'constraints_source: computed'`. Grain: one row per area_id.

{% if var('constraints_source') == 'computed' %}
-- The loaded real table may predate the explicit-status schema. Its source is
-- nevertheless known: both inputs are England-only, and the historical roll-up
-- contains one numeric row per covered English MSOA. Derive status from that
-- invariant so Welsh zero/low placeholders can never leak through as evidence.
select
    area_id,
    case when area_id like 'W%' then null else cast(planning_constraint_count as integer) end
        as planning_constraint_count,
    case
        when area_id like 'W%' then 'not_covered'
        when planning_constraint_count is null then 'source_missing'
        else 'covered'
    end as planning_source_status,
    'Planning Data platform' as planning_source_name,
    case when area_id like 'W%' then null else lower(trim(flood_risk_flag)) end
        as flood_risk_flag,
    case when area_id like 'W%' then null else cast(flood_postcode_pct as double) end
        as flood_postcode_pct,
    case
        when area_id like 'W%' then 'not_covered'
        when flood_postcode_pct is null then 'source_missing'
        else 'covered'
    end as flood_source_status,
    'Environment Agency flood risk zones' as flood_source_name
from {{ source('constraints', 'area_constraints') }}
{% else %}
select
    area_id,
    cast(planning_constraint_count as integer) as planning_constraint_count,
    lower(trim(planning_source_status)) as planning_source_status,
    planning_source_name,
    lower(trim(flood_risk_flag)) as flood_risk_flag,
    cast(flood_postcode_pct as double) as flood_postcode_pct,
    lower(trim(flood_source_status)) as flood_source_status,
    flood_source_name
from {{ ref('ref_area_constraints_sample') }}
{% endif %}
