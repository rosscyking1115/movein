"""The terminal asset: export the decision marts to the slim API extract.

Wraps scripts/build_decision_db.py. Depends on the two decision marts (via the
dbt asset graph), so Dagster only rebuilds data/decision.duckdb after they have
been refreshed. Committing that file to main is what triggers the existing
.github/workflows/refresh.yml deploy — this asset produces its input.
"""

from dagster import AssetExecutionContext, MaterializeResult, asset
from dagster_dbt import get_asset_key_for_model

from .dbt_assets import movein_dbt_models
from .resources import DATA_DIR


@asset(
    group_name="export",
    compute_kind="duckdb",
    deps=[
        get_asset_key_for_model([movein_dbt_models], "rpt_neighbourhood_score"),
        get_asset_key_for_model([movein_dbt_models], "rpt_area_profile_mvp"),
    ],
    description=(
        "Export rpt_neighbourhood_score + rpt_area_profile_mvp from the "
        "warehouse into data/decision.duckdb — the slim read-only extract the "
        "API ships."
    ),
)
def decision_extract(context: AssetExecutionContext) -> MaterializeResult:
    import build_decision_db  # scripts/build_decision_db.py

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
