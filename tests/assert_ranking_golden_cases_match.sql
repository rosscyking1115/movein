-- The seed mirrors contracts/neighbourhood-scoring-v2-cases.json and executes
-- the shared score-descending, area-id-ascending tie order inside dbt/DuckDB.
with ranked as (

    select
        *,
        row_number() over (
            partition by case_name
            order by score desc nulls last, area_id asc
        ) as actual_position
    from {{ ref('ref_ranking_golden_cases') }}

)

select *
from ranked
where actual_position != expected_position
