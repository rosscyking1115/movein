# Project Audit And Housing Fit

Date checked: 2026-06-25

## Verdict

This project is suitable to adapt into the proposed renter-first UK housing decision-support tool, but the right move is a new product built on this repo's engineering spine, not a light rename of the current dashboard.

The current project is already a strong analytics-engineering portfolio piece: HM Land Registry Price Paid data, DuckDB, dbt, tested marts, dbt docs, Streamlit, GitHub Actions, and a small dashboard database extract. The housing decision-support idea needs the same spine, but with finer geography, new public datasets, user preference modelling, and explainable scoring.

Recommended direction:

- Keep this repo as the current polished "UK property analytics" proof unless you intentionally want to replace it.
- Fork or branch into a new product repo named something like `uk-housing-decision-support`.
- Reuse the ingestion, dbt, DuckDB, CI, docs, and Streamlit deployment patterns.
- Replace the market-study reporting marts and dashboard pages with renter/mover decision marts and workflows.

## What I Verified

Local checks completed:

- `uv run python -m compileall scripts dashboard`: passed.
- Dashboard DuckDB smoke check: passed. It contains `analytics.rpt_price_yoy_by_region`, `analytics.rpt_top_postcodes_by_volume`, and `analytics.rpt_new_build_premium`.
- Dashboard data sanity check: `rpt_price_yoy_by_region` has 50 rows for 2021-2025; London 2025 YoY is `-1.0`; North East 2025 new-build premium is `61.8`.
- Historical baseline: `uv run dbt build --target dev` passed with 10 models, 88 data tests, 1 seed, 1 source, and 1 exposure before the YoY hardening test was added.
- `uv run dbt build --target dev --profiles-dir .`: passed after adding the fixture-backed MSOA geography slice, with 14 models, 154 data tests, 2 seeds, 1 source, and 1 exposure.
- `uv run dbt source freshness --target dev --profiles-dir .`: executed successfully. Local full data produced a warning because it has not been reloaded within the 35-day warning window; the CI/docs sample loads immediately before the freshness check, so it should pass cleanly there.
- `uv run python -m unittest tests.test_download_raw`: passed. It covers downloader config-year selection, explicit-year overrides, skip behaviour, and verifies forced refresh preserves the existing Parquet if the fresh download fails.
- `uv run sqlfluff lint models/ --dialect duckdb --templater dbt`: passed.
- `uv pip check`: passed.

Previously flagged local environment warning:

- Fixed: `requests` no longer warns about transitive HTTP package versions. `requirements.txt` now pins `chardet==5.2.0`, and `tests/test_dependency_imports.py` fails if `requests` emits an import warning again.

## Current Strengths

- Clear analytics layering: raw source to staging view, ephemeral intermediate model, core marts, reporting marts, dashboard.
- Strong dbt discipline: declared grains, column docs, relationship tests, singular tests, value tests, and an exposure for the Streamlit dashboard.
- Practical local warehouse choice: DuckDB is cheap, portable, and appropriate for a public-data portfolio project.
- Deployment strategy is sensible: a full warehouse for dbt work, plus a small committed `data/dashboard.duckdb` for Streamlit Cloud.
- The README tells a coherent project story with business questions, architecture, test coverage, and source attribution.

## Bugs And Things To Flag

### 1. Dashboard extract was not validated in CI

The dashboard reads `data/dashboard.duckdb` directly from `dashboard/_utils.py:19`. That database is built by `scripts/build_dashboard_db.py`, which exports three marts listed in `scripts/build_dashboard_db.py:28`. The CI workflow now smoke-tests the committed dashboard extract, rebuilds a sample extract after `dbt build`, and smoke-tests that generated extract too.

Why it matters:

- The dbt warehouse can pass while the deployed dashboard database is stale.
- A renamed mart column could break Streamlit without CI catching it.

Recommended fix:

- Status: fixed by adding `scripts/smoke_dashboard_db.py` and dashboard extract build/smoke steps to `.github/workflows/ci.yml`.
- Keep this smoke test updated when Streamlit starts reading new marts or columns.

### 2. Dashboard About page overstated the test count

The README previously said the project had 88 data tests at `README.md:130`, and the local `dbt build` confirmed 88 data tests before YoY hardening. After adding YoY, date-spine, and fixture-backed MSOA geography/profile tests, the expected count is 154 data tests, and the README plus dashboard copy now use that count.

Why it matters:

- This is a visible credibility issue in the deployed app.
- It makes the project look less carefully maintained than it is.

Recommended fix:

- Status: fixed by updating `README.md`, `.github/workflows/ci.yml`, `.github/workflows/docs.yml`, and `dashboard/pages/4_About.py` to the 154-test count.
- Add a small dashboard text smoke check or keep these counts out of hard-coded UI copy.

### 3. CI sample does not properly exercise YoY logic

Originally, `scripts/download_raw.py:145` made `--sample` download only the max configured year. CI used that sample in `.github/workflows/ci.yml:75`. The YoY mart uses `lag(...)` in `models/marts/analytics/rpt_price_yoy_by_region.sql:46`, but a one-year sample leaves YoY fields null. The singular test in `tests/assert_rpt_yoy_pct_within_bounds.sql:14` only checks non-null YoY values, so the one-year CI path could pass without testing real year-over-year behaviour.

Why it matters:

- A YoY regression could pass CI.
- The headline dashboard logic depends on 2024 vs 2025 calculations.

Recommended fix:

- Status: fixed by making `--sample` use the latest two complete years and adding `tests/assert_rpt_yoy_has_expected_rows.sql`.

### 4. The project analysis window needed central config

Hard-coded year assumptions appeared in:

- `scripts/download_raw.py` previously had a separate `DEFAULT_YEARS = [2021, 2022, 2023, 2024, 2025]`. It now reads `landreg_start_year` and `landreg_end_year` from `dbt_project.yml`; `--sample` selects the latest two configured years.
- `models/marts/core/dim_date.sql` previously hard-coded the date spine to `2020-01-01` through `2026-12-31`. It now derives the spine from `landreg_start_year` and `landreg_end_year`, with one buffer year on either side.
- `models/marts/core/_models.yml` previously tested `transferred_year` between literal 2021 and 2025. This is now controlled by `landreg_start_year` and `landreg_end_year` in `dbt_project.yml`.
- `dashboard/streamlit_app.py` previously expected 2025 and 2024 for headline metrics. This is now fixed: the home page derives the latest and prior years from the loaded marts.
- `README.md:162`: future work says to rerun with `--years 2026`, but the model tests and dashboard assumptions are not ready for 2026.

Why it matters:

- The current project will become stale.
- The housing decision-support idea needs rolling refreshes and variable analysis windows.

Recommended fix:

- Status: fixed for downloader defaults by making `scripts/download_raw.py` read `landreg_start_year` and `landreg_end_year` from `dbt_project.yml`.
- Status: fixed for dbt model/test bounds by adding `landreg_start_year` and `landreg_end_year` vars in `dbt_project.yml`.
- Status: fixed for the dashboard headline, snapshot tabs, and mart spot-check helper by deriving latest and prior years from the loaded marts.
- Status: fixed for date-spine maintenance by deriving the buffer dates from the configured Land Registry years and adding `tests/assert_dim_date_covers_configured_window.sql`.

### 5. Geography is too coarse for decision support

The current region join is based on postcode area. The key logic is in `models/intermediate/int_transactions__enriched.sql:34` and joins `ref_postcode_area_region` at `models/intermediate/int_transactions__enriched.sql:51`.

Why it matters:

- Region and postcode-area analysis is fine for a market overview.
- It is not enough for "where should I live?" decisions.
- Commute, crime, EPC, flood, planning, and amenity data need decision-grade geography. The MVP contract now selects MSOA as the canonical recommendation grain, with LSOA/postcode/local-authority data rolling into or annotating MSOA.

Recommended fix:

- Status: started by adding `ref_onspd_sample`, `stg_geo__postcodes`, `dim_postcode_geography`, `dim_area`, and `rpt_area_profile_mvp`.
- Status: started for ingestion by adding `scripts/prepare_onspd_seed.py`, which normalizes a local ONSPD-style CSV/ZIP into the geography seed contract.
- Prefer official postcode lookup data for postcode to local authority, LSOA, MSOA, region, and coordinates, then measure Land Registry postcode coverage against the full local snapshot.
- Keep postcode-area rollups only as a broad fallback.

### 6. Land Registry refresh semantics were weak

`scripts/download_raw.py` skips a yearly Parquet if it already exists unless `--force-refresh` is passed. Forced refresh downloads and converts to a temporary Parquet first, then replaces the cached file only after success. The source includes `record_status`, and `models/staging/stg_landreg__transactions.sql:60` keeps it, but downstream logic does not yet use it to resolve changed or deleted records.

Why it matters:

- HM Land Registry releases are updated monthly and can update earlier data.
- A cached yearly file can miss corrections unless the operator deliberately runs `--force-refresh`.
- For the current portfolio project this is tolerable if documented. For a decision-support product, refresh semantics must be explicit.

Recommended fix:

- Status: fixed for manual refresh by adding `--force-refresh` and unit tests for skip/failure behaviour.
- Store source release metadata.
- Decide whether to use full snapshot replacement or dedupe by latest transaction record.

### 7. Source freshness was configured but not gated

`models/staging/_sources.yml:14` uses `_loaded_at` for freshness, with 35-day and 90-day thresholds at `models/staging/_sources.yml:16`. The GitHub workflows now run `dbt source freshness --target dev` after loading the sample and before `dbt build`, so freshness is enforced in both PR CI and docs generation.

There is also a semantic issue: `_loaded_at` proves when the local loader ran, not necessarily whether the upstream Land Registry release is current.
Local full-data runs may warn if the warehouse has not been reloaded within 35 days; CI should be clean because it loads the sample immediately before checking freshness.

Recommended fix:

- Keep `_loaded_at` as lineage.
- Status: fixed for CI by adding `dbt source freshness` to `.github/workflows/ci.yml` and `.github/workflows/docs.yml`.
- Add upstream release date tracking per source.
- Report freshness in the dashboard and docs per source.

### 8. Internal docs conflicted on the standard-transaction filter

`models/marts/core/fct_transactions.sql:28` previously said the standard-transaction filter excludes about 3-5 percent of rows. The README says it excludes about 16 percent at `README.md:73`, and the local row counts support about 16 percent. The SQL comment now avoids the stale fixed percentage and explains the reason for filtering instead.

Why it matters:

- The README explanation is credible, but the model comment conflicts with it.
- Interviewers sometimes read SQL comments first; conflicting numbers weaken trust.

Recommended fix:

- Status: fixed by rephrasing the model comment without the stale 3-5 percent claim.

## Suitability For The Housing Idea

Fit score: 8/10 for engineering reuse, 9/10 for project opportunity.

Why yes:

- The proposed idea is still housing/public-data analytics.
- dbt + DuckDB + Streamlit is an appropriate MVP stack.
- Existing project already proves ingestion, transformation, marts, tests, docs, and deployment.
- The user-facing gap is real: public data is fragmented across house prices, rents, crime, energy, transport, flood risk, planning, and listings.

Why it cannot be a simple rebrand:

- Current outputs answer market analyst questions, not renter/mover questions.
- Sale-price data is useful context but not enough for renters.
- Current geography is too broad for commute/risk/lifestyle decisions.
- The new product needs user inputs, weighted preferences, confidence scores, explanations, and source caveats.

## Reuse vs Replace

Reuse:

- DuckDB warehouse pattern.
- dbt project structure.
- Source to staging to intermediate to marts flow.
- Test style and singular tests.
- Streamlit app deployment.
- Slim dashboard database extract.
- README/source attribution discipline.

Replace:

- Current three reporting marts.
- Current chart-first dashboard UX.
- Postcode-area seed as the main geography layer.
- Static 2021-2025 dashboard/headline assumptions. Fixed for the home page headline, snapshot charts, and `scripts/check_marts.py`.
- One-year CI sample. Fixed by making `--sample` use two years.

Add:

- Official rent statistics.
- EPC/energy data.
- Crime/safety indicators.
- Flood and planning constraints.
- Commute modelling.
- Amenity/access indicators.
- User-entered listing comparison.
- Explainable, weighted neighbourhood scoring.
- Data coverage and confidence indicators.

## Hiring-Manager Impression

Strongest proof:

- The current repo is credible analytics-engineering proof because it has a real public dataset, tests, docs, CI, and a deployed dashboard.

Weakest proof:

- The current dashboard is descriptive. It does not yet show product thinking, user preferences, or decision support.

Evidence gaps:

- Streamlit render smoke is now checked with `streamlit.testing.v1.AppTest` for the home page and all dashboard pages.
- Dashboard database drift is now checked by the smoke script. Browser-level visual confidence is now covered by a Playwright smoke test that loads the dashboard, asserts visible content, takes a screenshot, and rejects a blank render.
- Geospatial modelling has started with a fixture-backed MSOA/postcode bridge, but it still needs a real official lookup snapshot and coverage threshold.
- No multi-source integration yet.

Must-fix before turning this into the housing tool:

- Finish the real geography grain. The chosen MVP grain is MSOA; the repo now has fixture-backed dbt models and a local official-lookup normalizer, but still needs the first pinned official snapshot and full coverage measurement.
- Add at least rent, commute, crime, EPC, and flood/planning source layers.
- Make the scoring explainable and caveated.
- Avoid claiming live rental market coverage unless user-entered or licensed listing data is used.
