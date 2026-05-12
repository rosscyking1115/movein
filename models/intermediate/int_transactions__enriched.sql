{{
    config(
        materialized='ephemeral'
    )
}}

-- Intermediate: enrich staging transactions with postcode-area extraction
-- and the regional join. Filtered to ppd_category='standard' so all
-- downstream marts see only arm's-length sales.
--
-- Why ephemeral: this CTE is small enough that we'd rather inline it into
-- every dependent mart than materialise an extra table. dbt resolves the
-- ref() into a CTE at compile time.

with transactions as (

    select * from {{ ref('stg_landreg__transactions') }}
    where ppd_category = 'standard'

),

postcode_parts as (

    select
        *,
        -- Outward code = everything before the space (e.g. 'SW1A 1AA' → 'SW1A')
        case
            when postcode is null then null
            when position(' ' in postcode) > 0
                then substr(postcode, 1, position(' ' in postcode) - 1)
            else postcode
        end as postcode_outward,

        -- Postcode area = leading 1 or 2 letters before any digit
        -- e.g. 'SW1A' → 'SW', 'B12' → 'B', 'EC1A' → 'EC'.
        case
            when postcode is null then null
            else regexp_extract(postcode, '^[A-Z]+', 0)
        end as postcode_area

    from transactions

),

with_region as (

    select
        pp.*,
        coalesce(rg.region, 'Unknown') as region
    from postcode_parts as pp
    left join {{ ref('ref_postcode_area_region') }} as rg
        on pp.postcode_area = rg.postcode_area

)

select * from with_region
