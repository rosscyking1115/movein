"""The dbt transform layer, loaded as Dagster assets.

`@dbt_assets` turns every model in the dbt project into an asset and every dbt
test into an asset check, with dbt's own lineage preserved. Because the
`landreg.transactions` source is remapped onto the warehouse_transactions asset
(see translator.py), the staging models depend directly on the ingestion output
— one continuous graph.
"""

from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from .resources import REAL_SOURCE_VARS_JSON, dbt_project
from .translator import HousingDecisionSupportDbtTranslator


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=HousingDecisionSupportDbtTranslator(),
)
def housing_decision_support_dbt_models(context: AssetExecutionContext, dbt: DbtCliResource):
    # --vars: the orchestrated build reads the real raw_* sources, matching the
    # vars the manifest was parsed with (resources.REAL_SOURCE_VARS). The
    # fixture-seed default stays the plain-dbt/CI path.
    # --threads 1: on Windows only one process can hold the DuckDB file in write
    # mode, and a parallel build deadlocks on the single-file write-lock.
    yield from dbt.cli(
        ["build", "--threads", "1", "--vars", REAL_SOURCE_VARS_JSON],
        context=context,
    ).stream()
