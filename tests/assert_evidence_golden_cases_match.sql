-- The seed mirrors contracts/neighbourhood-scoring-v2-cases.json and makes the
-- categorical evidence contract executable in dbt as well as Python/TypeScript.
with calculated as (

    select
        *,
        case
            when available_component_count < 3
                or crime_population_denominator is null
                or planning_source_status is distinct from 'covered'
                or flood_source_status is distinct from 'covered'
                then 'limited'
            when available_component_count = 5
                and rent_source_grain = 'msoa'
                and median_sale_price_confidence = 'reliable'
                and all_component_source_dates_known
                and rent_reference_date is not null
                and crime_population_reference_date is not null
                and crime_period_start is not null
                and crime_period_end is not null
                then 'strong'
            else 'mixed'
        end as actual_level
    from {{ ref('ref_evidence_golden_cases') }}

)

select *
from calculated
where actual_level is distinct from expected_level
