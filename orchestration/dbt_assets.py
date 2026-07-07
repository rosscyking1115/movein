"""The dbt transform layer, loaded as Dagster assets.

`@dbt_assets` turns every model in the dbt project into an asset and every dbt
test into an asset check, with dbt's own lineage preserved. Because the
`landreg.transactions` source is remapped onto the warehouse_transactions asset
(see translator.py), the staging models depend directly on the ingestion output
— one continuous graph.
"""

from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from .resources import dbt_project
from .translator import MoveInDbtTranslator


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=MoveInDbtTranslator(),
)
def movein_dbt_models(context: AssetExecutionContext, dbt: DbtCliResource):
    # --threads 1: on Windows only one process can hold the DuckDB file in write
    # mode, and a parallel build deadlocks on the single-file write-lock.
    yield from dbt.cli(["build", "--threads", "1"], context=context).stream()
