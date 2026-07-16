"""Top-level Dagster definitions for the housing decision-support pipeline.

Load with:  dagster dev -m orchestration.definitions
"""

from __future__ import annotations

from dagster import (
    AssetSelection,
    DefaultScheduleStatus,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
)

from . import checks, export_assets, ingest_assets, reference_assets
from .dbt_assets import housing_decision_support_dbt_models
from .resources import dbt_resource

# The whole refresh as one launchable run: ingest → dbt → extract. Steps are
# serialized (max_concurrent: 1) because the warehouse is a single DuckDB file
# and Windows allows one writer — parallel ingest steps would collide on the
# write-lock. Order still comes from the asset graph, so "serialized" only
# costs parallelism the file could never offer anyway.
full_refresh_job = define_asset_job(
    name="full_refresh",
    selection=AssetSelection.all(),
    config={"execution": {"config": {"multiprocess": {"max_concurrent": 1}}}},
    description=(
        "Run the entire monthly refresh — ingest all six sources, build the "
        "dbt project with real-source vars, export the decision extract."
    ),
)

# The cadence the pipeline is designed for, defined in code but deliberately
# STOPPED: the archives behind the prepared_* assets are large/licensed and
# refreshed manually, so pretending an unattended cron works would be theatre.
# Land Registry publishes around the 20th working day, hence the 28th.
monthly_refresh_schedule = ScheduleDefinition(
    job=full_refresh_job,
    cron_schedule="0 9 28 * *",
    default_status=DefaultScheduleStatus.STOPPED,
    description=(
        "Monthly full refresh, aligned to the Land Registry publication "
        "cadence. Defined to document the SLA; switched off because the "
        "reference-source archives are fetched manually."
    ),
)

defs = Definitions(
    assets=[
        ingest_assets.raw_landreg_ppd,
        ingest_assets.warehouse_transactions,
        *reference_assets.prepared_file_specs,
        *reference_assets.reference_load_assets,
        housing_decision_support_dbt_models,
        export_assets.decision_extract,
    ],
    asset_checks=[checks.raw_landreg_ppd_is_sane],
    jobs=[full_refresh_job],
    schedules=[monthly_refresh_schedule],
    resources={"dbt": dbt_resource},
)
