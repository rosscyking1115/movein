# MoveIn

**An explainable decision-support tool for where to live in England & Wales —
honest neighbourhood indicators built from official open data, served by a tested
dbt + DuckDB engine through a public API and website.**

MoveIn reads a neighbourhood (MSOA grain, 7,264 areas) and lays it out like a
surveyor's schedule: five 0–100 indicators — affordability, safety, energy, flood
resilience, convenience — **and the raw figure behind every score**, with a
weighted overall that re-ranks to your priorities, per-area confidence, and source
caveats. Not a price predictor and not a listings site: an honest decision layer
over fragmented official UK datasets. Indicators only — never a "safe/unsafe"
verdict.

> *MoveIn* is the product; `uk-housing-decision-support` is the repository.

[![CI](https://github.com/rosscyking1115/uk-housing-decision-support/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rosscyking1115/uk-housing-decision-support/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-informational.svg)](LICENSE)

## Live

| Surface | URL |
|---|---|
| 🌐 **MoveIn website** (Next.js / Vercel) | https://uk-housing-decision-support.vercel.app |
| ⚙️ **API** (FastAPI / Fly.io) — OpenAPI docs | https://uk-housing-decision-support-api.fly.dev/docs |
| 📊 **dbt docs** (lineage + column catalogue) | https://rosscyking1115.github.io/uk-housing-decision-support/ |

## Architecture

One engine, many clients. The dbt + DuckDB warehouse produces a small read-only
`decision.duckdb` extract; the API serves it; the MoveIn website (and a planned
mobile app) are HTTP clients of the same typed contract.

```text
  dbt + DuckDB engine  ──►  data/decision.duckdb  ──►  API (FastAPI, api/)
  (9 open-data sources)        (slim extract)            │  /v1 + OpenAPI
                                                         │
                                          ┌──────────────┴──────────────┐
                                   MoveIn website (web/)        Mobile app (Expo)
                                      Next.js · Vercel               planned
```

Nothing is reimplemented per client: the re-ranking/scoring logic in
[`api/scoring.py`](api/scoring.py) mirrors the warehouse mart
(`rpt_neighbourhood_score`), and the website re-ranks client-side from the same
component scores for instant slider response. Design rationale lives in
[`PRODUCT_ROADMAP.md`](PRODUCT_ROADMAP.md).

## Repository layout

| Path | What |
|---|---|
| `models/` | dbt models: sources → staging → intermediate → marts (the engine). |
| `seeds/`, `macros/`, `snapshots/`, `analyses/` | dbt seeds (fixtures + name lookups), macros, snapshots, analyses. |
| `scripts/` | Data prep/load scripts for the real (non-fixture) sources. |
| `tests/` | 189 dbt data tests + the API test suite (`tests/test_api.py`). |
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
every push. Nine national open-data signals are rolled up to MSOA grain.

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
scoring (`rpt_neighbourhood_score`) turns these into five 0–100 percentile
component scores, a weighted overall that re-ranks on user weights, per-area
confidence from coverage, and a "why this area" line. Door-to-door commute *time*
is the one remaining planned signal (station proximity is already covered).

Geography, the source toggles, and the full per-source prep commands are detailed
in [`HOUSING_DECISION_SUPPORT_DATA_SOURCES.md`](HOUSING_DECISION_SUPPORT_DATA_SOURCES.md)
and the [Source attribution](#source-attribution) section.

## Running locally

### 1. The engine (dbt + DuckDB)

```bash
git clone https://github.com/rosscyking1115/uk-housing-decision-support.git
cd uk-housing-decision-support
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |  macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip && pip install -r requirements.txt
dbt deps

mkdir -p ~/.dbt && cp profiles.yml.example ~/.dbt/profiles.yml   # one-time

python scripts/download_raw.py     # --sample for a faster 2-year run
python scripts/load_to_duckdb.py
dbt seed
dbt build                          # full warehouse + 189 data tests, < 5 min on a laptop
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
(incl. the API suite), `dbt build` with **189 data tests**, source-freshness, and
sqlfluff lint.

| Layer | Count | What it catches |
|---|---|---|
| Source freshness | 1 | Stale upstream data (warn if nothing newer than 35 days). |
| Built-in row-shape | 137 | Schema bugs, FK orphans, enum drift. |
| `dbt-utils` | 21 | Sign/range invariants, multi-column uniqueness, score bounds. |
| `dbt-expectations` | 14 | Type-cast bugs, statistical drift, format regressions. |
| Singular (`tests/assert_*.sql`) | 17 | Domain anomalies, coverage and coherence guards. |
| **dbt total** | **189** | All passing on every `dbt build`. |
| API (`tests/test_api.py`) | 8 | Endpoint contract, search re-rank, coverage 404/422, mocked postcodes.io. |

## Product principles

- Explain trade-offs; never hide behind one opaque score.
- No "safe"/"unsafe" labels — measured indicators and caveats only.
- No red-to-green good/bad colouring of scores; the EPC A–G bands are the one
  official exception.
- Official and open data first; no portal scraping. Listing comparison is user-entered.
- Area-level guidance over individual-property claims unless the source supports it.
- Missing data lowers confidence — it never silently becomes a zero.

## Roadmap

Phased plan in [`PRODUCT_ROADMAP.md`](PRODUCT_ROADMAP.md). Current state:

- **Phase 0 — data quick wins** ✅ manual listing checker + ONS per-bedroom rent.
- **Phase 1 — API** ✅ **deployed** (Fly.io).
- **Phase 2 — Website** ✅ **deployed** (Vercel): the MoveIn UI — search, compare,
  listing checker, and ~7k programmatic area/town/region/rent pages.
- **Phase 3 — Mobile (Expo)** ⬜ planned; the standout feature is Rightmove share-in.
- **Cross-cutting** ✅ retired the legacy Streamlit apps; data-refresh deploy
  automated. ⬜ analytics; custom domain + Search Console; door-to-door commute time.

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
