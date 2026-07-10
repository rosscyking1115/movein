# MoveIn

**A tested dbt + DuckDB pipeline that turns
seven official UK open-data sources into explainable, documented neighbourhood
indicators — with published lineage, 197 data tests + 2 dbt unit tests, and a
reproducible fixture-to-full build.**

The engine rolls fragmented public housing data up to a consistent MSOA grain
(7,264 England & Wales neighbourhoods) and derives five transparent 0–100
indicators — affordability, safety, energy, flood resilience, convenience — each
kept **beside the raw figure it came from**, with per-area confidence driven by
data coverage. Missing data lowers confidence; it never silently becomes a zero.
The "where to live" framing is the *vehicle* — the substance is the **pipeline,
the dimensional + decision modelling, the tests, and the explainability layer**.

> **Scope.** A reference analytics-engineering project, not a product — the UK
> area-data space is already well served (CrystalRoof, Plumplot, PostcodeCheck, …).
> It's an end-to-end data stack built over official open data.
>
> *MoveIn* is the working name; `movein` is the repository.

[![CI](https://github.com/rosscyking1115/movein/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rosscyking1115/movein/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-informational.svg)](LICENSE)

![MoveIn homepage — every 0–100 score shown beside the raw figure behind it (rent, crime rate, EPC), laid out like a surveyor's trade-off receipt](.github/assets/hero.png)

## Live

| Surface | URL |
|---|---|
| 🌐 **MoveIn website** (Next.js / Vercel) | https://uk-housing-decision-support.vercel.app |
| ⚙️ **API** (FastAPI / Fly.io) — OpenAPI docs | https://uk-housing-decision-support-api.fly.dev/docs |
| 📊 **dbt docs** (lineage + column catalogue) | https://rosscyking1115.github.io/movein/ |

## Architecture

**The dbt + DuckDB warehouse is the centre of gravity.** It builds a small
read-only `decision.duckdb` extract that a thin FastAPI service serves; a Next.js
website is one HTTP client of it. The clients exist to show the modelling is
frontend-agnostic and genuinely consumable — they are not the point.

```text
  dbt + DuckDB engine  ──►  data/decision.duckdb  ──►  API (FastAPI, api/)
  (7 open-data sources)        (slim extract)            │  /v1 + OpenAPI
                                                         │
                                                  Website (web/, Next.js)
                                                  — a thin demo client
```

The transformation lives in exactly one place: the scoring logic in
[`api/scoring.py`](api/scoring.py) mirrors the warehouse mart
(`rpt_neighbourhood_score`), so no business logic is reimplemented per client.
(A Streamlit MVP and an Expo mobile client were also built and are now parked —
see the roadmap.)

## Repository layout

| Path | What |
|---|---|
| `models/` | dbt models: sources → staging → intermediate → marts (the engine). |
| `seeds/`, `macros/`, `analyses/` | dbt seeds (fixtures + name lookups), reusable macros (`haversine_km`, `median_anchored`), ad-hoc analyses. |
| `scripts/` | Data prep/load scripts for the real (non-fixture) sources. |
| `orchestration/` | **Dagster asset graph** over the monthly refresh: ingestion (+ a pre-dbt data-quality gate) → dbt → decision extract. |
| `tests/` | 197 dbt data tests + 2 dbt unit tests + the API test suite (`tests/test_api.py`). |
| `api/` | **FastAPI service** over the decision marts (resolve / search / listing-check / areas index / meta). `Dockerfile` + `fly.toml`. |
| `web/` | **MoveIn website** — Next.js. Search, compare, listing checker, and ~7k programmatic area/town/region/rent pages. See [`web/README.md`](web/README.md) and [`web/DESIGN_BRIEF.md`](web/DESIGN_BRIEF.md). |
| `data/` | Local DuckDB warehouse + the committed `decision.duckdb` extract the API ships. |
| `DEPLOY.md` | Runbook for deploying the API (Fly.io) and website (Vercel). |

The four planning docs at the repo root carry the full reasoning:
[`PROJECT_AUDIT_AND_HOUSING_FIT.md`](PROJECT_AUDIT_AND_HOUSING_FIT.md),
[`HOUSING_DECISION_SUPPORT_BUILD_PLAN.md`](HOUSING_DECISION_SUPPORT_BUILD_PLAN.md),
[`HOUSING_AREA_PROFILE_CONTRACT.md`](HOUSING_AREA_PROFILE_CONTRACT.md),
[`HOUSING_DECISION_SUPPORT_DATA_SOURCES.md`](HOUSING_DECISION_SUPPORT_DATA_SOURCES.md).

## The data engine

A complete, tested analytics-engineering pipeline is the project's credibility:
sources → staging → intermediate → marts (dimensions / facts / reporting), tested
at every layer, with lineage and column-level docs published to GitHub Pages on
every push. Seven official open-data sources are rolled up to MSOA grain.

| Signal | Coverage | Notes |
|---|---|---|
| Sale-market context (HM Land Registry) | 4.99M transactions, 2021–2025 | Long-term market layer; median sale price per area. |
| Geography (ONSPD) | 2.73M postcodes → 7,264 E&W MSOAs | 99.999% Land Registry coverage; readable area/LA/region names. |
| Rent + affordability (ONS PIPR) | 100% of MSOAs | Local-authority rent incl. **per-bedroom** (1/2/3/4+). |
| Energy (EPC) | 100% (23.5M certificates) | Per-area median EPC band. |
| Crime (Police API) | 99.6% (17.1M crimes) | Approx. monthly rate per 1,000 — indicator only. |
| Flood + planning (planning.data.gov.uk) | 100% | Spatial point-in-polygon; flood band + constraint count. |
| Convenience (OpenStreetMap) | 100% (437k amenities) | Nearest supermarket/school/GP/park/station + walkable count. |

Each external source is **fixture-default for fast, reproducible CI**, with a
real-data toggle (`--vars '<source>: …'`) for production builds. Explainable
scoring (`rpt_neighbourhood_score`) turns these into five 0–100 component scores,
a weighted overall, per-area confidence from coverage, and a "why this area" line.
Door-to-door commute *time* is the one remaining planned signal (station proximity
is already covered).

Geography, the source toggles, and the full per-source prep commands are detailed
in [`HOUSING_DECISION_SUPPORT_DATA_SOURCES.md`](HOUSING_DECISION_SUPPORT_DATA_SOURCES.md)
and the [Source attribution](#source-attribution) section.

### How a recommendation is explained

The score is a transformation you can read top to bottom, not a black box —
implemented in [`rpt_neighbourhood_score`](models/marts/decision/rpt_neighbourhood_score.sql):

1. **Per-indicator normalisation → 0–100.** Continuous indicators (rent-to-income
   ratio, crime rate, station distance) use a **median-anchored, winsorised
   min-max** via the [`median_anchored`](macros/median_anchored.sql) macro: clip to
   the 2nd/98th percentile, then map p2→0, median→50, p98→100. This keeps
   *magnitude* (unlike a pure percentile rank, which forces a uniform spread and
   makes every area look extreme). Categorical/absolute indicators use fixed
   anchors — EPC band (A=100 … G=0), flood = share of postcodes in a flood zone.
2. **Overall = weighted _geometric_ mean** of the indicators an area actually has
   (floored at 1), so one excellent pillar can't mask a poor one. Weights are
   configurable via dbt `vars`; a client can re-weight from the stored component
   scores without recomputing the marts.
3. **Missing indicators are dropped, never zeroed** — an absent signal lowers the
   area's `confidence_level` (`high`/`medium`/`low` from coverage) instead of
   silently penalising it.
4. **Every score ships beside its raw figure** (rent, crime rate, EPC band) and a
   generated `why_this_area` sentence, so the output is auditable.

Because it's one SQL transformation, the logic is covered by the same data tests
as everything else (score bounds 0–100, coherence, coverage-vs-confidence).

## Orchestration (Dagster)

Land Registry data refreshes monthly, so the refresh is modelled as a
**Dagster asset graph** ([`orchestration/`](orchestration/)) rather than a
sequence of hand-run scripts: six ingestion assets (the Land Registry spine is
downloaded automatically; five reference sources load from locally prepared
files) feed the whole dbt project — loaded via `dagster-dbt`, so every model is
an asset and every dbt test an asset check in the same lineage — and end at
`decision_extract`, the slim DuckDB file the API ships.

<p align="center">
  <img src="docs-assets/dagster-lineage.svg" alt="Dagster asset lineage: six ingestion sources feeding the dbt transform layer and the decision extract" width="720">
</p>

Two design points worth reading the code for:

- **Data-quality gates *before* dbt.** dbt tests run after load; every
  ingestion asset is gated *before* it. The raw Land Registry parquet is
  validated in [`orchestration/checks.py`](orchestration/checks.py) (row-count
  floor, price/date null-flood, malformed-postcode rate), and each reference
  source carries a `prepared_file_is_sane` check evaluated **before its
  drop-and-recreate load** — without it, a truncated prepared file would
  replace a good warehouse table. A failed gate halts the graph at the front
  door instead of propagating into the marts.
- **The orchestrated build is the real refresh.** It parses *and* builds dbt
  with the real-source vars, while plain `dbt build` keeps the fixture-seed
  default for fast, reproducible CI. One `full_refresh` job runs the whole
  pipeline (steps serialized — DuckDB is a single-writer file on Windows).

Why Dagster and not Airflow: this is a set of data assets with lineage, not a
task DAG — the asset/materialization model fits, and dbt lineage flows into the
same graph. Freshness is declared (35-day warn on the warehouse spine and the
extract, mirroring dbt's source freshness) and a monthly schedule is defined in
code — but ships **switched off**: the full source archives are large/licensed
and refreshed manually, so the job runs on demand
(`dagster dev -m orchestration.definitions`) — pretending a scheduler runs in
production would be theatre. Details and trade-offs in
[`orchestration/README.md`](orchestration/README.md).

## Running locally

### 1. The engine (dbt + DuckDB)

```bash
git clone https://github.com/rosscyking1115/movein.git
cd movein
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |  macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip && pip install -r requirements.txt
dbt deps

mkdir -p ~/.dbt && cp profiles.yml.example ~/.dbt/profiles.yml   # one-time

python scripts/download_raw.py     # --sample for a faster 2-year run
python scripts/load_to_duckdb.py
dbt seed
dbt build                          # full warehouse + 197 data tests, < 5 min on a laptop
```

### 2. The API

```bash
.venv/Scripts/python -m uvicorn api.main:app --reload   # http://127.0.0.1:8000/docs
```

### 3. The MoveIn website

```bash
cd web
cp .env.example .env.local          # points at http://127.0.0.1:8000
npm install && npm run dev          # http://localhost:3000
```

The website needs the API running. Full web docs in [`web/README.md`](web/README.md);
deploying both services is covered in [`DEPLOY.md`](DEPLOY.md).

## Testing & CI

`ci.yml` runs on every PR and gates `main` via branch protection: Python unit tests
(incl. the API suite), `dbt build` with **197 data tests + 2 unit tests**,
source-freshness, and sqlfluff lint.

| Layer | Count | What it catches |
|---|---|---|
| Source freshness | 1 | Stale upstream data (warn if nothing newer than 35 days). |
| Built-in row-shape | 145 | Schema bugs, FK orphans, enum drift, contract violations. |
| `dbt-utils` | 21 | Sign/range invariants, multi-column uniqueness, score bounds. |
| `dbt-expectations` | 14 | Type-cast bugs, statistical drift, format regressions. |
| Singular (`tests/assert_*.sql`) | 17 | Domain anomalies, coverage and coherence guards. |
| **dbt data-test total** | **197** | All passing on every `dbt build`. |
| dbt **unit** tests | 2 | Model *logic* on mock inputs: enrichment (postcode parse + region join + filter) and the scoring maths (median-anchored min-max, geometric-mean floor, missing-component rule). |
| API (`tests/test_api.py`) | 8 | Endpoint contract, search re-rank, coverage 404/422, mocked postcodes.io. |

## Modelling & scoring principles

- Explain trade-offs; never hide behind one opaque score.
- No "safe"/"unsafe" labels — measured indicators and caveats only.
- No red-to-green good/bad colouring of scores; the EPC A–G bands are the one
  official exception.
- Official and open data first; no portal scraping. Listing comparison is user-entered.
- Area-level guidance over individual-property claims unless the source supports it.
- Missing data lowers confidence — it never silently becomes a zero.

## Roadmap

The roadmap is about **engineering depth, not product
surface.** Built and stable: the dbt + DuckDB engine (this repo), a FastAPI
service ([`api/`](api/)), and a Next.js site ([`web/`](web/)) as a thin client. A
Streamlit MVP and an Expo mobile client were also built and are **parked** — the
clients aren't the point.

Analytics-engineering improvements planned (deepening the modelling):

- **Decompose the decision marts** into an `int_area__*` intermediate layer —
  `rpt_area_profile_mvp` and `rpt_neighbourhood_score` currently carry the joins +
  scoring inline; splitting them improves testability and lineage granularity.
- **Model contracts** (`contract: enforced`) on the decision marts — they are the
  API's schema of record.
- **Incremental materialisation** for `fct_transactions` over the ~5M Land
  Registry rows.
- A **snapshot** (SCD-2) of ONS rent across data vintages.
- Door-to-door **commute time** as an additional indicator (station proximity is
  already covered).

Historical product framing is preserved in [`PRODUCT_ROADMAP.md`](PRODUCT_ROADMAP.md).

## Source attribution

All sources are public and used under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
(OpenStreetMap under the Open Database Licence). Per-source access and prep
commands are catalogued in
[`HOUSING_DECISION_SUPPORT_DATA_SOURCES.md`](HOUSING_DECISION_SUPPORT_DATA_SOURCES.md).

- [HM Land Registry Price Paid Data](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads) — sale-market context. Contains HM Land Registry data © Crown copyright and database right.
- [ONS Postcode Directory](https://geoportal.statistics.gov.uk/) — postcode → MSOA/LSOA/LA/region geography and name lookups. Contains OS, ONS, Royal Mail and NRS data © Crown copyright and database right.
- [ONS Price Index of Private Rents](https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics) — local-authority rent (incl. per bedroom). Values may be provisional and revised.
- [Energy Performance Certificates](https://get-energy-performance-data.communities.gov.uk/) — per-area median EPC band (23.5M certificates). Certificates may be expired or superseded.
- [Police street-level crime](https://data.police.uk/data/) — approximate monthly crime rate per 1,000 (LSOA→MSOA), as an indicator only.
- [Planning Data Platform](https://www.planning.data.gov.uk/) — per-MSOA planning-constraint count and flood-risk band, via spatial point-in-polygon.
- [OpenStreetMap](https://www.openstreetmap.org/) (via [Geofabrik](https://download.geofabrik.de/)) — nearest-amenity + walkable count. © OpenStreetMap contributors, Open Database Licence.

## License

[MIT](LICENSE).
