{{
    config(
        materialized='view',
        description='One row per Land Registry transaction with types cast and columns renamed. No business logic.'
    )
}}

-- Staging layer for HM Land Registry Price Paid transactions.
--
-- Job of this model: cast types, rename columns to analytics-ready names,
-- light cleanup (postcode normalisation, NULLs for empty strings). NO joins,
-- NO derived business measures, NO filtering beyond an obvious data-hygiene
-- guard (kit-sanctioned: drop price = 0 / negative junk from historic data).
--
-- Codes are NOT decoded to human labels here — that belongs in the dim_*
-- models in Phase 3 so a single change-of-label edit lands in one place.

with source as (

    select * from {{ source('landreg', 'transactions') }}

),

renamed as (

    select
        -- Identifiers
        transaction_id,

        -- Measures + dates
        cast(price as bigint)                                  as price_gbp,
        cast(date_of_transfer as date)                         as transferred_on,

        -- Postcode: upper-case + trim removes inconsistent whitespace and
        -- mixed casing in the source; nullif drops the rare empty postcode.
        nullif(upper(trim(postcode)), '')                      as postcode,

        -- Coded categorical fields — kept as raw codes here, decoded in dim_ models.
        nullif(property_type, '')                              as property_type_code,
        nullif(old_new, '')                                    as is_new_build_flag,
        nullif(duration, '')                                   as tenure_code,

        -- Address parts: nullif so empty strings don't pollute downstream string concat.
        nullif(paon, '')                                       as primary_address,
        nullif(saon, '')                                       as secondary_address,
        nullif(street, '')                                      as street,
        nullif(locality, '')                                    as locality,
        nullif(town_city, '')                                   as town_city,
        nullif(district, '')                                    as district,
        nullif(county, '')                                      as county,

        -- ppd_category_type IS a tiny lookup (only A/B), so decoding it inline
        -- in staging is fair game — saves a 2-row dim that nobody would join.
        case ppd_category_type
            when 'A' then 'standard'
            when 'B' then 'additional'
            else null
        end                                                    as ppd_category,

        -- Record status (A=add / C=change / D=delete) — keep raw for now.
        nullif(record_status, '')                              as record_status,

        -- Lineage timestamp from the loader (UTC ISO-8601 string in source).
        cast(_loaded_at as timestamp)                          as _loaded_at

    from source

    -- Data hygiene guard: Land Registry has a handful of price=0 historic
    -- transfers (e.g. compulsory purchase orders, charity transfers) that
    -- are technically valid but break price-based analytics.
    where cast(price as bigint) > 0

)

select * from renamed
