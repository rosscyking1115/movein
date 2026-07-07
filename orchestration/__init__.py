"""Dagster orchestration for the MoveIn analytics pipeline.

Models the monthly Land Registry refresh as an asset graph:

    raw_landreg_ppd  →  warehouse_transactions  →  [dbt: staging → marts]  →  decision_extract

so the previously-implicit order of hand-run scripts + dbt commands becomes an
explicit, lineage-tracked graph with a data-quality gate at ingestion.

Load it with:  dagster dev -m orchestration.definitions
"""
