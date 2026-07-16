"""The terminal asset: export the decision marts to the slim API extract.

Wraps scripts/build_decision_db.py. Depends on the two decision marts (via the
dbt asset graph), so Dagster only rebuilds data/decision.duckdb after they have
been refreshed. Committing that file to main is what triggers the existing
.github/workflows/refresh.yml deploy — this asset produces its input.
"""

from datetime import timedelta

from dagster import AssetExecutionContext, FreshnessPolicy, MaterializeResult, asset
from dagster_dbt import get_asset_key_for_model

from .dbt_assets import housing_decision_support_dbt_models
from .resources import DATA_DIR, load_script


@asset(
    group_name="export",
    compute_kind="duckdb",
    deps=[
        get_asset_key_for_model([housing_decision_support_dbt_models], "rpt_neighbourhood_score"),
        get_asset_key_for_model([housing_decision_support_dbt_models], "rpt_area_profile_mvp"),
    ],
    # The extract the API serves goes stale on the same monthly cadence as the
    # sources feeding it — same thresholds as the warehouse spine.
    freshness_policy=FreshnessPolicy.time_window(
        fail_window=timedelta(days=90), warn_window=timedelta(days=35)
    ),
    description=(
        "Export rpt_neighbourhood_score + rpt_area_profile_mvp from the "
        "warehouse into data/decision.duckdb — the slim read-only extract the "
        "API ships."
    ),
)
def decision_extract(context: AssetExecutionContext) -> MaterializeResult:
    build_decision_db = load_script("build_decision_db")

    return_code = build_decision_db.main()
    if return_code != 0:
        raise RuntimeError(
            f"build_decision_db.py exited {return_code} — see logs above."
        )

    extract = DATA_DIR / "decision.duckdb"
    size_kb = extract.stat().st_size / 1024 if extract.exists() else 0
    return MaterializeResult(
        metadata={
            "extract_path": str(extract.relative_to(DATA_DIR.parent)),
            "size_kb": round(size_kb, 1),
        }
    )
