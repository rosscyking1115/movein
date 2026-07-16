"""Custom dbt→Dagster translation.

Two adjustments to the defaults:

  * Remap every dbt *source* onto the ingestion asset that loads it, so
    ingestion → dbt lineage is one continuous graph rather than disconnected
    islands. The manifest is parsed with the real-source vars (see
    resources.REAL_SOURCE_VARS), so all six sources appear in the graph.
  * Group every dbt model under ``transform`` so the UI reads
    ingest → transform → export.
"""

from typing import Any, Mapping, Optional

from dagster import AssetKey
from dagster_dbt import DagsterDbtTranslator

# (source_name, table_name) in models/staging/_sources.yml → the Python asset
# in ingest_assets.py / reference_assets.py that materializes that table.
SOURCE_TO_INGEST_ASSET = {
    ("landreg", "transactions"): "warehouse_transactions",
    ("geo", "onspd_postcodes"): "warehouse_geography",
    ("police", "street_crime"): "warehouse_crime",
    ("epc", "certificates"): "warehouse_epc",
    ("amenities", "area_access"): "warehouse_amenities",
    ("constraints", "area_constraints"): "warehouse_constraints",
}


class HousingDecisionSupportDbtTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        if dbt_resource_props["resource_type"] == "source":
            ingest_asset = SOURCE_TO_INGEST_ASSET.get(
                (dbt_resource_props.get("source_name"), dbt_resource_props["name"])
            )
            if ingest_asset:
                return AssetKey([ingest_asset])
        return super().get_asset_key(dbt_resource_props)

    def get_group_name(
        self, dbt_resource_props: Mapping[str, Any]
    ) -> Optional[str]:
        if dbt_resource_props["resource_type"] == "model":
            return "transform"
        return super().get_group_name(dbt_resource_props)
