"""Smoke tests for the Dagster orchestration definitions.

CI installs the Dagster stack but nothing else imports `orchestration/`, so
without this test an import error or a broken source-remap would only surface
the next time someone runs `dagster dev` locally. These tests load the real
Definitions and assert the lineage contract that makes the graph one piece:
every dbt source is remapped onto the ingestion asset that loads it.

Requires dbt to be installed with packages (`dbt deps`) and a profiles.yml in
place (CI stages both before the unit-test step); the dbt manifest is parsed
on demand if missing.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class OrchestrationDefinitionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # @dbt_assets needs target/manifest.json at import time. Parse with the
        # real-source vars — the manifest must wire staging to the raw_* sources
        # (not the fixture seeds) or the ingestion assets would be disconnected.
        from orchestration.resources import DBT_EXECUTABLE, REAL_SOURCE_VARS_JSON

        # Always replace an ambient manifest: a preceding fixture dbt build
        # writes a valid manifest whose staging parents are seeds, which is the
        # wrong lineage contract for the orchestrated real-source graph.
        subprocess.run(
            [
                DBT_EXECUTABLE,
                "parse",
                "--quiet",
                "--no-partial-parse",
                "--vars",
                REAL_SOURCE_VARS_JSON,
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )

    def test_every_dbt_source_is_remapped_onto_its_ingestion_asset(self) -> None:
        from dagster import AssetKey

        from orchestration.definitions import defs

        graph = defs.resolve_asset_graph()
        expected_edges = {
            ("staging", "stg_landreg__transactions"): "warehouse_transactions",
            ("staging", "stg_geo__postcodes"): "warehouse_geography",
            ("staging", "stg_crime__street"): "warehouse_crime",
            ("staging", "stg_epc__certificates"): "warehouse_epc",
            ("staging", "stg_amenities__area"): "warehouse_amenities",
            ("staging", "stg_constraints__area"): "warehouse_constraints",
        }
        for staging_key, ingest_asset in expected_edges.items():
            parents = {
                parent.to_user_string()
                for parent in graph.get(AssetKey(list(staging_key))).parent_keys
            }
            self.assertIn(
                ingest_asset,
                parents,
                f"{staging_key[1]} should depend on {ingest_asset}; "
                f"got {sorted(parents)} — the source remap in "
                "orchestration/translator.py is broken or the manifest was "
                "parsed with fixture vars.",
            )

    def test_extract_depends_on_both_decision_marts(self) -> None:
        from dagster import AssetKey

        from orchestration.definitions import defs

        parents = {
            parent.to_user_string()
            for parent in defs.resolve_asset_graph()
            .get(AssetKey(["decision_extract"]))
            .parent_keys
        }
        self.assertEqual(
            parents,
            {"decision/rpt_area_profile_mvp", "decision/rpt_neighbourhood_score"},
        )

    def test_full_refresh_job_covers_the_whole_pipeline(self) -> None:
        from orchestration.definitions import defs

        job = defs.resolve_job_def("full_refresh")
        node_names = {node.name for node in job.nodes}
        self.assertLessEqual(
            {
                "raw_landreg_ppd",
                "warehouse_transactions",
                "warehouse_geography",
                "warehouse_crime",
                "warehouse_epc",
                "warehouse_amenities",
                "warehouse_constraints",
                "housing_decision_support_dbt_models",
                "decision_extract",
            },
            node_names,
        )

    def test_ingestion_gates_are_registered(self) -> None:
        from orchestration.definitions import defs

        check_names = {
            key.to_user_string()
            for key in defs.resolve_asset_graph().asset_check_keys
        }
        self.assertIn("raw_landreg_ppd:raw_landreg_ppd_is_sane", check_names)
        for source in ("geography", "crime", "epc", "amenities", "constraints"):
            self.assertIn(f"warehouse_{source}:prepared_file_is_sane", check_names)


if __name__ == "__main__":
    unittest.main()
