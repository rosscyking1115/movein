# uk-housing-decision-support

**An explainable UK neighbourhood decision-support tool for renters and movers —
built on a tested, public-data analytics-engineering spine.**

The goal: given a household's income, budget, commute target, and risk tolerance,
rank neighbourhoods (MSOA grain) as transparent trade-offs — affordability,
commute, safety indicators, energy, flood/planning risk, and long-term market
context — with confidence levels and source caveats on every recommendation.
Not a price predictor, and not a glossy listings site: an honest decision layer
over fragmented official UK datasets.

> **Status: MVP feature-complete.** Nine real, national open-data signals —
> sales, geography, rent/affordability, EPC energy, crime, planning, flood, and
> convenience — feed an explainable per-MSOA scoring engine
> (`rpt_neighbourhood_score`) and a renter-facing Streamlit app (`app/`). Each
> external source is **fixture-default for fast, reproducible CI**, with a
> real-data toggle for production builds. Door-to-door commute *time* is the one
> remaining MVP source (station proximity is already covered). Indicators only —
> never a "safe/unsafe" verdict.

## Live links

- 📊 **dbt docs site (lineage + column catalogue):** https://rosscyking1115.github.io/uk-housing-decision-support/
- 📈 **Streamlit dashboard (legacy market-study UI):** https://ross-uk-property-analytics.streamlit.app/
- ✅ **CI status:** [![CI](https://github.com/rosscyking1115/uk-housing-decision-support/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rosscyking1115/uk-housing-decision-support/actions/workflows/ci.yml) — every PR runs Python unit tests, Streamlit render/browser smoke tests, source freshness, `dbt build`, 189 data tests, dashboard extract smoke tests, and sqlfluff lint. Branch protection on `main` requires the check to pass before merging.

## Project status

| Capability | State | Notes |
|---|---|---|
| Analytics-engineering spine (dbt + DuckDB + CI + docs) | ✅ Built | Inherited from the market-study project; hardened in this pivot |
| Land Registry sale-market context | ✅ Built | 4.99M transactions, 2021–2025, tested marts |
| Geography (MSOA `dim_area`, postcode bridge) | ✅ Built | Real ONSPD May 2026 lookup (2.73M postcodes → 7,264 England & Wales MSOAs), readable area/LA/region names, 99.999% Land Registry coverage; committed fixture is the CI default |
| `rpt_area_profile_mvp` (raw per-area facts) | ✅ Built | The nine signals per MSOA: sale context, rent + affordability, EPC, crime, planning, flood, amenity access |
| Explainable scoring (`rpt_neighbourhood_score`) | ✅ Built | 5 component scores (affordability / safety / energy / flood / convenience, 0–100 percentile) + a weighted `overall_score` that **re-ranks when the user shifts weights**, per-area confidence from coverage, and a "why this area" summary |
| ONS rent + affordability | ✅ Built | PIPR local-authority rent (May 2026) on **7,262/7,264 (100%)** of E&W MSOAs; affordability ratio vs a default income scenario |
| EPC energy profile | ✅ Built | 23.5M England & Wales certificates → per-area median EPC band + certificate count on **100%** of MSOAs (median band D); committed fixture is the CI default, real bulk via `--vars 'epc_source: bulk'` |
| Crime safety indicator | ✅ Built | 17.1M police street-crimes (LSOA→MSOA) → approx. monthly rate per 1,000 on **99.6%** of MSOAs (median ~6.6, indicator only — never a safe/unsafe label); committed fixture is the CI default, real bulk via `--vars 'crime_source: bulk'` |
| Flood + planning constraints | ✅ Built | Spatial point-in-polygon (2.7M postcode centroids × planning.data.gov.uk geometries) → per-MSOA planning_constraint_count (0–119) + flood band on **100%** of MSOAs (~23% medium/high flood); committed fixture is the CI default, real roll-up via `--vars 'constraints_source: computed'` |
| Convenience / amenities (OSM) | ✅ Built | Spatial roll-up of 437k OpenStreetMap amenities (nodes + way centroids) → per-MSOA nearest supermarket/school/GP/park/station + walkable-essentials count on 100% of MSOAs; committed fixture is the CI default, real via `--vars 'amenities_source: computed'` |
| Door-to-door commute time | ⬜ Planned | Station proximity is already in the amenities layer; journey-time routing (TfL London-first) is the remaining refinement |
| Renter-facing decision app (`app/`) | ✅ Built | Streamlit workflow: set income/budget/priorities → live-reranked shortlist, per-area trade-off receipt, compare, **a listing checker** (postcode + asking price → area + price-vs-local), and sources & caveats. Reads the committed `data/decision.duckdb` extract |

The full reasoning lives in four planning docs at the repo root:

- [`PROJECT_AUDIT_AND_HOUSING_FIT.md`](PROJECT_AUDIT_AND_HOUSING_FIT.md) — audit of the inherited spine and its fit for the new product.
- [`HOUSING_DECISION_SUPPORT_BUILD_PLAN.md`](HOUSING_DECISION_SUPPORT_BUILD_PLAN.md) — phased plan, target architecture, and module strategy.
- [`HOUSING_AREA_PROFILE_CONTRACT.md`](HOUSING_AREA_PROFILE_CONTRACT.md) — why MSOA, the `dim_area`/`dim_postcode_geography`/`rpt_area_profile_mvp` column contracts, and the geography test contract.
- [`HOUSING_DECISION_SUPPORT_DATA_SOURCES.md`](HOUSING_DECISION_SUPPORT_DATA_SOURCES.md) — the official/open sources, access, grain, priority, and caveats.

## Product principles

- Explain trade-offs; never hide behind one opaque score.
- No "safe"/"unsafe" labels — measured indicators and caveats only.
- Official and open data first; no portal scraping. Listing comparison is user-entered.
- Area-level guidance over individual-property claims unless the source supports it.
- Show source freshness and coverage on every recommendation; make uncertainty visible.
- Missing data lowers confidence — it does not silently become a zero.

## What's already built (the engineering spine)

The new product reuses a complete, tested analytics-engineering pipeline. This is
the part that already works end-to-end and gives the project its credibility.

Sources → staging → intermediate → marts (dimensions / facts / reporting),
tested at every layer, with lineage and column-level docs published to GitHub
Pages on every push. The original product question was a 5-year UK housing
**market study** on HM Land Registry Price Paid data (every recorded England &
Wales transaction 2021–2025, ≈4.99M rows). Those reporting marts —
`rpt_price_yoy_by_region`, `rpt_top_postcodes_by_volume`,
`rpt_new_build_premium` — now serve as the **long-term market-context layer**
for the decision tool rather than the headline product.

```mermaid
flowchart LR
  src[("HM Land Registry<br/>Price Paid CSV<br/>(2021–2025)")]
  onspd[(ref_onspd_sample<br/>geography fixture)]
  stg[stg_landreg__transactions]
  stg_geo[stg_geo__postcodes]
  int{{int_transactions__enriched}}
  fct[fct_transactions<br/>4.18M rows]
  dpg[dim_postcode_geography]
  area[dim_area<br/>MSOA grain]
  rptm[rpt_*_market_context<br/>YoY / top postcodes / new-build]
  prof[rpt_area_profile_mvp<br/>decision prototype]

  src --> stg --> int --> fct --> rptm
  onspd --> stg_geo --> dpg --> area
  fct --> prof
  area --> prof
```

## Tech choices

| Layer | Tool | Why |
|---|---|---|
| Warehouse | **DuckDB** | Free, zero-ops, single-file, runs in CI. The whole 5-year warehouse fits in ~200 MB; queries return in milliseconds. |
| Transform | **dbt-core 1.11** + **dbt-duckdb 1.10** | Industry-standard analytics-engineering tooling, declared grains, tested marts, lineage. |
| Tests | **Built-in** + **dbt-utils** + **dbt-expectations** + **singular** | Row-shape, value-shape, and named-hypothesis tests. 189 data tests + 1 source-freshness check. |
| Docs | `dbt docs` → **GitHub Pages** | Free hosting, lineage graph, column-level catalogue (`.github/workflows/docs.yml`). |
| App | **Streamlit** | Python-native, read-only DuckDB connection, free Community Cloud hosting. The renter-facing decision workflow (Phase 5) will replace the current chart dashboard. |
| CI | **GitHub Actions** | `ci.yml` runs unit tests, Streamlit smoke tests, source freshness, `dbt build`, 189 data tests, dashboard extract smoke, and sqlfluff lint on every PR. `docs.yml` publishes dbt docs to Pages. Branch protection on `main` gates merges. |
| Lint | **sqlfluff 4.1** + dbt templater | Wired via `pre-commit` (local) and as a hard CI gate. |

`requirements.txt` pins are verified against PyPI for Python 3.13 (`cp313`) wheels
so a fresh clone needs no source builds — which matters on Windows.

## Test coverage

| Layer | Count | What it catches |
|---|---|---|
| Source freshness | 1 | Stale upstream data (warn if no rows newer than 35 days) |
| Built-in row-shape (`not_null`, `unique`, `accepted_values`, `relationships`) | 137 | Schema bugs, FK orphans, enum drift |
| `dbt-utils` (`expression_is_true`, `unique_combination_of_columns`) | 21 | Sign / range invariants, multi-column uniqueness, score bounds |
| `dbt-expectations` (range, regex, length, distinct, quantile, row count) | 14 | Type-cast bugs, statistical drift, format regressions |
| Singular (`tests/assert_*.sql`) | 17 | Domain anomalies — non-vacuous YoY, date-spine coverage, area-profile market-match/source-caveat/small-sample/rent/EPC/crime-coherence guards, and Land Registry → MSOA coverage |
| **Total** | **189** | All passing on every `dbt build`; source freshness is a separate CI gate |

## Geography

Decision support needs finer geography than the legacy postcode-area region join.
The MVP grain is **MSOA**: `stg_geo__postcodes` → `dim_postcode_geography` →
`dim_area`, with `rpt_area_profile_mvp` joining Land Registry sale context onto
areas. Two interchangeable sources sit behind the same column contract,
selected by the `geo_source` var:

- **`fixture` (default):** the tiny committed `ref_onspd_sample` seed (6
  postcodes) — keeps CI and fresh clones fast and reproducible.
- **`onspd`:** the full national ONS Postcode Directory snapshot
  (**2.73M postcodes → 7,264 England & Wales MSOAs**), giving **99.999% Land
  Registry postcode coverage**. Enforced by
  `tests/assert_landreg_postcode_coverage.sql` (≥95% threshold; a no-op on
  fixture builds).

Raw ONS codes are turned into readable names (`E02006959` → *Salford 033*,
`E12000007` → *London*, `W99999999` → *Wales*) by joining three small committed
seeds (`ref_msoa_names`, `ref_lad_names`, `ref_region_names`), extracted from the
ONSPD documents with `scripts/prepare_geo_name_seeds.py`.

The full ONSPD is large and licence-restricted, so it is never committed. Prepare
and load a local snapshot, then build against it:

```bash
# 1. Normalise an official ONSPD CSV/ZIP into the geography contract (gitignored)
python scripts/prepare_onspd_seed.py path/to/ONSPD.zip --member "Data/ONSPD_*_UK.csv" --snapshot-date 2026-05-01
# 2. (one-time per ONSPD release) refresh the small name seeds
python scripts/prepare_geo_name_seeds.py path/to/ONSPD.zip
# 3. Load the postcode lookup into the warehouse as raw_geo.onspd_postcodes
python scripts/load_geography.py
# 4. Build the geography + decision layer against the real lookup
dbt build --vars 'geo_source: onspd'
```

Real geography handles the messy edges honestly: the grain is restricted to
England & Wales MSOAs (matching Land Registry), so Scottish Intermediate Zones
(`S02…`) and ONS pseudo-codes (e.g. `L99999999`) are treated as "no MSOA"
rather than fake areas, and ONSPD no-grid-reference sentinel coordinates are
nulled rather than used as real locations.

## How to run from a fresh clone

```bash
# 1. Clone + venv
git clone https://github.com/rosscyking1115/uk-housing-decision-support.git
cd uk-housing-decision-support
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |  macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
dbt deps

# 2. Profile (one-time)
mkdir -p ~/.dbt
cp profiles.yml.example ~/.dbt/profiles.yml

# 3. Pull data + load + build (5-year default ~3-5 min, --sample for a fast 2-year run)
python scripts/download_raw.py     # use --sample for a faster 2-year run
python scripts/load_to_duckdb.py
dbt seed
dbt build
```

A fresh clone reproduces the full warehouse + 189 data tests in under 5 minutes
on a laptop. To re-publish docs locally: `dbt docs generate && dbt docs serve`.

## Roadmap

The phased plan lives in [`HOUSING_DECISION_SUPPORT_BUILD_PLAN.md`](HOUSING_DECISION_SUPPORT_BUILD_PLAN.md). In short:

1. **Spine hardening** — ✅ done (this pivot).
2. **Geography foundation** — ✅ done: real ONSPD snapshot, 99.999% Land Registry coverage, decision marts keyed on `area_id`, readable names.
3. **MVP data sources** — ONS rent ✅; EPC energy ✅ (23.5M certificates); crime ✅ (17.1M police crimes); flood + planning ✅ (spatial point-in-polygon); convenience/amenities ✅ (437k OSM amenities → nearest-amenity + walkable count). Only door-to-door commute time remains (station proximity already covered).
4. **Decision marts** — ✅ done: `rpt_neighbourhood_score` — explainable 0–100 component scores, a weighted overall that re-ranks on user weights, per-area confidence/coverage, and "why this area" fragments.
5. **Renter-facing app** — ✅ done (`app/`): income/budget/priority inputs, a live-reranked shortlist, per-area trade-off receipt, side-by-side compare, and a sources & caveats page. Run with `streamlit run app/streamlit_app.py`.
6. **Quality gates** — score-bound, coverage, and explanation-completeness tests; UI accessibility review.
7. **Deployment** — Streamlit Cloud + GitHub Pages + slim committed extract.

Known prototype caveats to address before anything is user-facing:

- `rpt_neighbourhood_score.confidence_level` is dynamic (per-area component coverage), but `rpt_area_profile_mvp.confidence_level` is still a hardcoded global `'low'` — the raw-facts mart's flag should be retired in favour of the score mart's.
- `affordability_ratio` uses a single default income scenario until the app collects a real user budget.
- No live rental-listing coverage is claimed or scraped — listing comparison will be user-entered.

## Source attribution

All sources are public and used under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

Loaded:

- [HM Land Registry Price Paid Data](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads) — sale-market context. Contains HM Land Registry data © Crown copyright and database right.
- [ONS Postcode Directory](https://geoportal.statistics.gov.uk/) — postcode → MSOA/LSOA/LA/region geography (and the MSOA/LA/region name lookups). Contains OS, ONS, Royal Mail and NRS data © Crown copyright and database right.
- [ONS Price Index of Private Rents](https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics) — local-authority average monthly rent. Values may be provisional and revised.
- [Energy Performance Certificates](https://get-energy-performance-data.communities.gov.uk/) — per-area median EPC band from 23.5M domestic certificates. Bulk download needs a free GOV.UK One Login; then `python scripts/prepare_epc_seed.py <download>`, `python scripts/load_epc.py`, `dbt build --vars 'epc_source: bulk'`. Certificates may be expired or superseded.

- [Police street-level crime](https://data.police.uk/data/) — per-area approximate monthly crime rate per 1,000 (LSOA→MSOA) from 17.1M crimes, as a measured indicator only, never a safe/unsafe label. Generate a bulk archive (no login), then `python scripts/prepare_crime_seed.py <download>`, `python scripts/load_crime.py`, `dbt build --vars 'crime_source: bulk'`.
- [Planning Data Platform](https://www.planning.data.gov.uk/) — per-MSOA planning-constraint count (conservation areas, green belt, Article 4, tree preservation zones) and flood-risk band, via spatial point-in-polygon. Datasets download directly (no login); `python scripts/prepare_area_constraints.py <csv_dir>` (DuckDB spatial roll-up; the 1.9 GB flood-risk-zone join is the slow part, ~10 min), `python scripts/load_constraints.py`, `dbt build --vars 'constraints_source: computed'`.
- [OpenStreetMap](https://www.openstreetmap.org/) (via a [Geofabrik](https://download.geofabrik.de/) extract) — per-MSOA convenience: nearest supermarket/school/GP/pharmacy/green space/station + walkable-essentials count, from 437k amenities (nodes + way centroids) via DuckDB `ST_ReadOSM` + spatial nearest-neighbour. `python scripts/prepare_amenity_access.py <pbf>`, `python scripts/load_amenities.py`, `dbt build --vars 'amenities_source: computed'`. © OpenStreetMap contributors, Open Database Licence.

Planned (TfL / transport,
OpenStreetMap) and their licences/caveats are catalogued in
[`HOUSING_DECISION_SUPPORT_DATA_SOURCES.md`](HOUSING_DECISION_SUPPORT_DATA_SOURCES.md).

## License

[MIT](LICENSE).
</content>
</invoke>
