-- The committed seed is mechanically checked against the versioned JSON contract
-- by tests/test_scoring_contract.py. This test executes every shared case in dbt.
with calculated as (

    select
        *,
        round(exp(
            (
                coalesce(affordability_weight * ln(greatest(affordability_score, 1)), 0)
                + coalesce(safety_weight * ln(greatest(safety_score, 1)), 0)
                + coalesce(energy_weight * ln(greatest(energy_score, 1)), 0)
                + coalesce(flood_weight * ln(greatest(flood_score, 1)), 0)
                + coalesce(convenience_weight * ln(greatest(convenience_score, 1)), 0)
            ) / nullif(
                (case when affordability_score is not null then affordability_weight else 0 end)
                + (case when safety_score is not null then safety_weight else 0 end)
                + (case when energy_score is not null then energy_weight else 0 end)
                + (case when flood_score is not null then flood_weight else 0 end)
                + (case when convenience_score is not null then convenience_weight else 0 end),
                0
            )
        ), 1) as actual_score
    from {{ ref('ref_scoring_golden_cases') }}

)

select *
from calculated
where actual_score is distinct from expected_score
