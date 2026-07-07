"""Custom dbt→Dagster translation.

Two adjustments to the defaults:

  * Remap the ``landreg.transactions`` dbt *source* onto the upstream Python
    asset ``warehouse_transactions``, so ingestion → dbt lineage is one
    continuous graph rather than two disconnected islands.
  * Group every dbt model under ``transform`` so the UI reads
    ingest → transform → export.
"""

from __future__ import annotations

from typing import Any, Mapping

from dagster import AssetKey
from dagster_dbt import DagsterDbtTranslator


class MoveInDbtTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        if (
            dbt_resource_props["resource_type"] == "source"
            and dbt_resource_props.get("source_name") == "landreg"
            and dbt_resource_props["name"] == "transactions"
        ):
            # Matches the key of the warehouse_transactions Python asset.
            return AssetKey(["warehouse_transactions"])
        return super().get_asset_key(dbt_resource_props)

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> str | None:
        if dbt_resource_props["resource_type"] == "model":
            return "transform"
        return super().get_group_name(dbt_resource_props)
