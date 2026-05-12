{{
    config(
        materialized='table'
    )
}}

-- fct_transactions — the project's headline fact table.
--
-- GRAIN: one row per arm's-length residential property sale recorded by
-- HM Land Registry in England + Wales for years 2021–2025.
-- (When asked in an interview to "walk through a model you're proud of",
--  this is the one — the explicit grain declaration is what sets a fact
--  table apart from a flat dump.)
--
-- SCALING NOTE: at the project's 4.2M-row size, a full table rebuild on
-- every `dbt build` completes in ~5s on a laptop, so `materialized='table'`
-- is the right call here. When this grows past ~50M rows or the rebuild
-- starts dominating CI time, the natural migration is to switch the
-- config to incremental (unique_key='transaction_key', on_schema_change
-- ='fail') and add an `is_incremental()` guard at the bottom of the
-- source CTE that filters to rows with `_loaded_at` greater than the
-- max already in `this`. The Parquet loader is already idempotent on
-- `_loaded_at`, so the incremental cut is clean — no risk of dropping
-- or duplicating rows across runs.
--
-- Filters:
--   - ppd_category = 'standard' (applied upstream in int_)  →
--     excludes ~3-5% of rows that are corrections, repossessions, charity
--     transfers, transfers under power of sale, etc. Those are real but
--     not 'market' transactions, and including them drags average price
--     down toward £1.
--
-- Surrogate key: dbt_utils.generate_surrogate_key on the natural key.
-- Per kit lesson L8, hashing avoids issues if the natural key gets reused
-- after an amendment, and is the convention reviewers expect on a fact.

with enriched as (

    select * from {{ ref('int_transactions__enriched') }}

)

select
    -- Surrogate key (PK)
    {{ dbt_utils.generate_surrogate_key(['transaction_id']) }} as transaction_key,

    -- Natural key (kept for traceability back to source)
    transaction_id,

    -- Foreign keys
    transferred_on as date_key,
    -- postcode_key is NULL for rare records with no postcode in the source
    -- (rather than a fake-NULL hash). Relationships test then skips them
    -- correctly, and dim_postcode stays clean (no synthetic 'Unknown' row).
    case
        when postcode is null
            then null
        else {{ dbt_utils.generate_surrogate_key(['postcode']) }}
    end as postcode_key,
    property_type_code,
    tenure_code,

    -- Measures
    price_gbp,
    case is_new_build_flag
        when 'Y' then true
        when 'N' then false
    end as is_new_build,

    -- Useful denormalised attributes for ad-hoc analysis
    transferred_on,
    extract(year from transferred_on)::int as transferred_year,
    extract(month from transferred_on)::int as transferred_month,
    region,
    postcode,
    postcode_area,
    town_city,
    district,

    -- Lineage
    _loaded_at

from enriched
