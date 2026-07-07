# Orchestration (Dagster)

Models the MoveIn data refresh as a **Dagster asset graph**, turning a sequence
of hand-run scripts + dbt commands into an explicit, lineage-tracked pipeline
with a **data-quality gate at ingestion**.

```
raw_landreg_ppd  ──►  warehouse_transactions  ──►  [dbt: staging → int → marts]  ──►  decision_extract
   (download)            (load to DuckDB)            (29 models, 197 tests)            (slim API extract)
      │
      └─ asset check: raw_landreg_ppd_is_sane  (row-count floor · null-flood · malformed-postcode rate)
```

This is a **first, thin slice**: it wires the real Land Registry spine
end-to-end. The other five sources (crime, EPC, geography, constraints,
amenities) are seed-backed in the default dbt build, so they flow through the
`[dbt]` stage without separate ingestion assets yet — those are the next fan-in.

## Why Dagster (and why not more)

- **Dagster, not Airflow** — the pipeline is a set of data assets with lineage,
  not a task DAG. `dagster-dbt` loads every dbt model as an asset and every dbt
  test as an asset check, so dbt's lineage flows into one graph.
- **DuckDB stays** — the data (4.99M Land Registry rows, 2021–2025) fits on one
  machine. No Snowflake/Spark; that would be cost and ops for no gain.
- **The genuinely new layer is the ingestion gate.** dbt tests run *after* load;
  `raw_landreg_ppd_is_sane` runs on the raw parquet *before* it enters the
  warehouse, catching a truncated file / null flood / malformed-postcode wave at
  the front door. It is a **blocking** check — a failure halts the graph.

## Layout

| File | What it holds |
| --- | --- |
| `definitions.py` | The `Definitions` — assets, the ingestion check, the dbt resource. |
| `resources.py` | Paths, the `DbtProject`/`DbtCliResource`, and env wiring. |
| `ingest_assets.py` | `raw_landreg_ppd`, `warehouse_transactions` (wrap the refresh scripts). |
| `dbt_assets.py` | `@dbt_assets` — the whole dbt project as one asset set. |
| `export_assets.py` | `decision_extract` — export the two decision marts to the API extract. |
| `checks.py` | `raw_landreg_ppd_is_sane` — the ingestion gate. |
| `translator.py` | Remaps the `landreg.transactions` dbt source onto `warehouse_transactions` so lineage is continuous. |

## Run it

```bash
# from the repo root, with the project venv active
dagster dev -m orchestration.definitions      # UI at http://127.0.0.1:3000
```

Assets are runnable **on demand** from the UI (Materialize). The local warehouse
is fixture-only and full source files are large/licensed, so this is not cron'd
in production — the graph models the refresh and runs when pointed at real data.

Once `decision_extract` writes `data/decision.duckdb`, committing that file to
`main` triggers the existing deploy half of the refresh
(`.github/workflows/refresh.yml` → Fly + Vercel).

### Config

`raw_landreg_ppd` takes optional run config:

```yaml
ops:
  raw_landreg_ppd:
    config:
      years: [2024, 2025]   # default: the window in dbt_project.yml
      force_refresh: false  # re-download even if the parquet exists
```

## Notes / gotchas

- **profiles.yml** resolves from `~/.dbt` (dbt's default). Override with
  `DBT_PROFILES_DIR` (e.g. in CI).
- **Windows DuckDB write-lock** — the dbt build runs `--threads 1`; a parallel
  build deadlocks on the single-file lock.
- **protobuf/grpc pins** — see `requirements.txt`; `grpcio-health-checking>=1.82`
  ships a protobuf-7.x gencode that breaks against dbt's `protobuf<7.0` cap.
