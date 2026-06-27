-- Risk: switching to the real ONSPD lookup could silently drop a large share
--       of Land Registry postcodes (format mismatch, stale or partial
--       snapshot), leaving area profiles with thin or biased market context.
--
-- Fail rows: one row if coverage of Land Registry postcodes onto an MSOA
-- area_id falls below min_postcode_coverage_pct. No-op on fixture builds,
-- where the 6-postcode seed is deliberately not national.

{% if var('geo_source') == 'onspd' %}

with coverage as (
    select
        count(*) as total_with_postcode,
        count(geo.area_id) as mapped_to_area
    from {{ ref('fct_transactions') }} as fct
    left join {{ ref('dim_postcode_geography') }} as geo
        on upper(trim(fct.postcode)) = geo.postcode
    where fct.postcode is not null
)

select
    total_with_postcode,
    mapped_to_area,
    round(100.0 * mapped_to_area / total_with_postcode, 2) as coverage_pct
from coverage
where
    100.0 * mapped_to_area / nullif(total_with_postcode, 0)
    < {{ var('min_postcode_coverage_pct') }}

{% else %}

select cast(null as bigint) as total_with_postcode
where false

{% endif %}
