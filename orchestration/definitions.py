"""Top-level Dagster definitions for the MoveIn pipeline.

Load with:  dagster dev -m orchestration.definitions
"""

from __future__ import annotations

from dagster import Definitions

from . import checks, export_assets, ingest_assets
from .dbt_assets import movein_dbt_models
from .resources import dbt_resource

defs = Definitions(
    assets=[
        ingest_assets.raw_landreg_ppd,
        ingest_assets.warehouse_transactions,
        movein_dbt_models,
        export_assets.decision_extract,
    ],
    asset_checks=[checks.raw_landreg_ppd_is_sane],
    resources={"dbt": dbt_resource},
)
