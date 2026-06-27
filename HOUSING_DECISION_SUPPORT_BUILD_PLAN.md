# Housing Decision Support Build Plan

Date prepared: 2026-06-25

## Skill Assessment

The eight skills are not equally useful for this project. I checked the installed local versions and applied the useful ones to this revised plan.

| Skill | Useful? | How to use it here |
|---|---:|---|
| `paper-context-resolver` | No, for now | It is for resolving narrow paper-reproduction gaps. Use only if we later reproduce a specific academic housing, geospatial, or recommender-system paper and need to confirm dataset splits, preprocessing, or evaluation protocol. |
| `repo-intake-and-plan` | No, for now | It is for README-first deep-learning repo reproduction. This repo has already been inspected and is not a model-reproduction repo. |
| `improve-codebase-architecture` | Yes, selectively | Use its architecture-review lens before implementation: identify deep modules, reduce shallow glue, and create clean modules for source ingestion, geography, scoring, and dashboard extraction. A full HTML architecture report is optional when we are ready to refactor/build. |
| `tdd` | Yes, strongly | Use vertical test-first slices for new behaviour: one failing test, one minimal implementation, then refactor. Especially important for dashboard DB validation, scoring, geography joins, and source freshness. |
| `requesting-code-review` | Yes | Add review checkpoints after each phase and before merge. For this plan-only update, no code reviewer is needed; for implementation PRs it should be mandatory. |
| `github-actions-docs` | Yes | Use official GitHub Actions docs when changing workflow syntax, permissions, events, schedules, concurrency, or artifacts. Relevant docs: workflow syntax, workflow events, workflows overview, and `GITHUB_TOKEN` permissions. |
| `frontend-design` | Yes | Use it when designing the renter-facing app so the product does not look like a generic dashboard. The UI should feel like a practical decision cockpit, not a marketing page. |
| `web-design-guidelines` | Yes | Use it as a UI review checklist: labels, focus states, semantic controls, keyboard handling, reduced motion, URL-reflected filters, accessible images, and robust content handling. |

Practical conclusion:

- Use `tdd`, `github-actions-docs`, `frontend-design`, `web-design-guidelines`, and `requesting-code-review` throughout implementation.
- Use `improve-codebase-architecture` before major structural work or when the repo starts feeling hard to navigate.
- Do not use the two AI-paper-reproduction skills unless this becomes a paper-reproduction task.

## Product Goal

Build an open UK housing decision-support tool for renters and movers.

Core question:

> Given my income, household needs, commute target, transport preferences, and risk tolerance, which neighbourhoods are the best trade-offs, and why?

This should not be "predict house prices with high accuracy." The useful product is an explainable decision layer over fragmented public datasets.

## MVP User Story

A user enters:

- Monthly household income after tax.
- Maximum comfortable rent.
- Household size and bedroom need.
- Work or study destination.
- Commute mode preference.
- Maximum commute time.
- Risk tolerance for flood, crime indicators, energy costs, and planning uncertainty.
- Optional listing details copied from a portal or landlord.

The app returns:

- Ranked areas or neighbourhoods.
- Affordability estimate.
- Commute estimate.
- Safety indicator profile.
- EPC/energy profile.
- Flood/planning risk flags.
- Long-term market context.
- "Why this area" explanations.
- Data coverage and confidence notes.

## Product Principles

- Explain trade-offs, do not hide behind one opaque score.
- Avoid "safe" or "unsafe" labels. Use measured indicators and caveats.
- Avoid scraping property portals unless there is explicit permission or a licensed API.
- Start with official and open data, then support user-entered listing comparison.
- Prefer area-level guidance over individual-property claims unless the source supports property-level use.
- Show source freshness and coverage on every recommendation.
- Build in vertical, test-first slices: one behaviour, one failing test, one implementation, then refactor.
- Treat the UI as the product, not a chart wrapper: every control should map to a renter decision.

## Recommended Repository Strategy

Option A, recommended:

- Keep this repo as `uk-property-analytics`.
- Create a new repo or long-lived branch for `uk-housing-decision-support`.
- Copy over the proven dbt/DuckDB/Streamlit/CI patterns.

Why:

- The current project is already a polished portfolio proof.
- The new product will change the story from "market analytics" to "decision support."
- A separate repo makes the portfolio cleaner: one analytics-engineering project, one product/geospatial decision-support project.

Option B:

- Adapt this repo directly.
- Only do this if you want the current project to evolve rather than remain a standalone proof.

## Target Architecture

```text
sources/
  land_registry_price_paid
  ons_private_rents
  ons_postcode_directory_or_geography_lookup
  epc_certificates
  police_street_crime
  planning_data
  flood_risk
  transport_nodes_or_commute_samples
  osm_amenities
  user_entered_listings

dbt models/
  staging/
    stg_landreg__transactions
    stg_ons__private_rents
    stg_geo__postcodes
    stg_epc__certificates
    stg_police__street_crime
    stg_planning__entities
    stg_flood__risk_zones
    stg_transport__nodes
    stg_osm__amenities
  intermediate/
    int_area__base
    int_area__rent_affordability
    int_area__commute
    int_area__crime_rates
    int_area__energy_profile
    int_area__flood_planning_flags
    int_area__market_context
  marts/core/
    dim_area
    dim_postcode_geography
    dim_date
    dim_transport_node
    fct_rent_market
    fct_sale_market
    fct_crime
    fct_epc
    fct_planning_constraint
  marts/decision/
    rpt_area_affordability
    rpt_area_commute
    rpt_area_risk_profile
    rpt_area_energy
    rpt_area_market_context
    rpt_neighbourhood_score
    rpt_tradeoff_explanations

app/
  Streamlit decision workflow
  comparison view
  source/caveat view
  user-entered listing evaluator
```

## Geography Contract

The MVP recommendation grain is MSOA. See `HOUSING_AREA_PROFILE_CONTRACT.md` for the concrete `dim_area`, `dim_postcode_geography`, `rpt_area_profile_mvp`, and test-contract decisions.

## Module Strategy

Use the architecture skill's "deep module" lens before adding more files. The goal is to keep simple interfaces around modules that hide real complexity.

Recommended modules:

- `sources/`: one command per external source, with source metadata and raw-to-Parquet conversion.
- `geography/`: postcode and area lookup logic, spatial joins, and coverage checks.
- `scoring/`: pure score component calculations and explanation fragments.
- `dashboard_extract/`: creates and validates the slim DuckDB used by Streamlit.
- `app/`: Streamlit UI only; no hidden data-cleaning or scoring logic in page files.

Avoid:

- Scattering source-specific caveats across dashboard pages.
- Putting scoring formulas directly inside Streamlit callbacks.
- Creating tiny helper modules whose interface is almost as complex as their implementation.
- Adding adapters for hypothetical sources before two real sources need the same interface.

## Phase 0: Preserve The Existing Project

Goal:

- Avoid breaking the current portfolio proof while planning the new product.

Tasks:

- Tag or commit the current passing state.
- Keep README links, dbt docs, and Streamlit dashboard intact.
- Decide whether the new product is a new repo or branch.

Exit criteria:

- Existing dbt build still passes.
- Existing Streamlit dashboard still reads `data/dashboard.duckdb`.

## Phase 1: Harden The Current Engineering Spine

Goal:

- Fix the review flags before building on top of the project.

Approach:

- Use TDD vertical slices. Start with a single failing smoke test for the dashboard DB, make it pass, then move to the next behaviour.
- Use official GitHub Actions docs before editing workflow syntax, triggers, permissions, schedules, concurrency, or artifact handling.
- Add a code-review checkpoint after the hardening PR before starting new housing-product features.

Tasks:

- Add a dashboard DB smoke test script. Done in `scripts/smoke_dashboard_db.py`.
- Add CI step to rebuild and validate `data/dashboard.duckdb`. Done in `.github/workflows/ci.yml`.
- Change CI sample from one year to at least two years. Done by making `--sample` select the latest two configured years.
- Add a YoY test requiring non-null YoY rows for non-first sample years. Done in `tests/assert_rpt_yoy_has_expected_rows.sql`.
- Fix dashboard About page hard-coded test-count copy. Done.
- Fix the `fct_transactions` comment that says the standard-transaction filter excludes 3-5 percent. Done by removing the stale fixed percentage.
- Add `dbt source freshness` as a CI or scheduled check. Done for the current repo's PR CI and docs workflow.
- Lint singular tests as well as `models/`, or document why only models are linted.
- Make dashboard headline year dynamic. Done for the home page headline, latest-year snapshot charts, and `scripts/check_marts.py`.
- Add `--force-refresh` to Land Registry downloader. Done with unit tests for skip/failure behaviour.
- Move years/date bounds into dbt variables or config. Done for dbt model/test bounds, downloader defaults, and the derived date spine buffer.
- Remove local `requests` dependency warning. Done by pinning `chardet==5.2.0` and adding a dependency import regression test.
- Add Streamlit render smoke tests. Done with `streamlit.testing.v1.AppTest` for the home page and all dashboard pages.
- Add browser/pixel-level dashboard smoke tests. Done with Playwright Chromium and a screenshot non-blank check.
- Add fixture-backed MSOA geography/profile slice. Done with `ref_onspd_sample`, `stg_geo__postcodes`, `dim_postcode_geography`, `dim_area`, and `rpt_area_profile_mvp`.
- Add local official postcode lookup preparation. Done with `scripts/prepare_onspd_seed.py`, which normalizes an ONSPD-style CSV/ZIP to the committed geography seed contract without committing the full lookup snapshot.

Suggested TDD slices:

1. Dashboard extract exists and contains required schemas/tables.
2. Dashboard extract required columns match Streamlit expectations.
3. Latest year and prior year are computed from data instead of hard-coded. Done for the dashboard headline, snapshot charts, and mart spot-check helper.
4. Two-year sample creates non-null YoY rows.
5. `--force-refresh` redownloads an existing yearly file and preserves the old Parquet if the fresh download fails. Done.
6. Source freshness command is present in CI or in a scheduled workflow. Done for the current repo.
7. Dependency import warnings fail fast in Python unit tests. Done for `requests`.
8. Streamlit pages render without app exceptions and expose expected title/data elements. Done.
9. Browser smoke loads the dashboard and rejects blank screenshots. Done.
10. Fixture-backed geography models prove the MSOA area contract. Done.
11. Official postcode lookup CSV/ZIP can be normalized into the geography seed contract. Done.

Suggested files:

- `scripts/smoke_dashboard_db.py`
- `scripts/download_raw.py`
- `.github/workflows/ci.yml`
- `models/marts/analytics/rpt_price_yoy_by_region.sql`
- `tests/assert_rpt_yoy_has_expected_rows.sql`
- `dashboard/streamlit_app.py`

GitHub Actions notes:

- GitHub defines workflows as YAML files containing one or more jobs; keep workflow changes explicit and small.
- Use `workflow_dispatch` for manual validation runs and `schedule` only for detached freshness/refresh checks.
- Set `permissions` narrowly when adding workflows. Avoid broad default token access unless needed.
- Use concurrency intentionally for PR validation so superseded runs cancel, but do not cancel Pages/data-refresh deployments halfway through.

Exit criteria:

- `dbt build` passes.
- `sqlfluff lint` passes.
- Dashboard DB smoke test passes.
- CI tests at least two years of data.

## Phase 2: Build The Geography Foundation

Goal:

- Replace broad postcode-area geography with decision-grade area modelling.

Preferred area grains:

- Postcode or outcode for search and user-entered listing matching.
- LSOA/MSOA for crime, deprivation, and local profiles where available.
- Local authority for rents and planning summaries.
- Region as a high-level fallback only.

Tasks:

- Add official postcode lookup ingestion. Done for local CSV/ZIP normalization; still needs a pinned first official snapshot choice.
- Build `dim_postcode_geography`. Done against the committed fixture.
- Build `dim_area` with area IDs, names, type, parent areas, latitude/longitude, and centroid. Done for fixture-backed MSOA-like areas.
- Create bridge tables from postcode to LSOA/MSOA/local authority/region.
- Add tests for postcode coverage, duplicate area IDs, invalid coordinates, and missing joins.

Suggested TDD slices:

1. A known postcode maps to local authority, LSOA/MSOA, region, and coordinates.
2. Invalid or retired postcodes are counted and surfaced, not silently dropped.
3. Land Registry transaction coverage exceeds a chosen threshold.
4. Area IDs are unique and stable.

Exit criteria:

- At least 95 percent of current Land Registry postcodes map to a local authority and LSOA/MSOA or an explicitly documented fallback.
- Decision marts use `area_id`, not only `postcode_area`.

## Phase 3: Add MVP Data Sources

Goal:

- Add enough public data to answer the renter/mover trade-off question.

MVP sources:

- HM Land Registry Price Paid Data for sale market context.
- ONS Private Rent and House Price data for rents and local affordability.
- EPC data for energy-efficiency distribution and likely energy-cost pressure.
- Police API data for crime indicator profiles.
- Planning Data API or bulk downloads for planning constraints and development context.
- Flood risk or flood warning area datasets for environmental risk flags.
- Transport data for commute estimates.
- User-entered listing data for "compare this listing" functionality.

Tasks:

- Create one ingestion script per source.
- Store raw files under `data/raw/<source>/`.
- Convert large CSV/JSON/GeoJSON files to Parquet.
- Add source metadata with download date, source release date, licence, and coverage notes.
- Add staging models per source.
- Add tests for row counts, required columns, area joins, and freshness.

Suggested TDD slices:

1. One source can be ingested from a cached fixture into raw Parquet.
2. One staging model exposes documented columns and source metadata.
3. Area join coverage is measured and fails below threshold.
4. Source freshness and source release date are visible in a mart.

Exit criteria:

- Each source has a reproducible ingestion command.
- Each source has source docs and caveats.
- Each source is represented in dbt lineage.

## Phase 4: Build Decision Marts

Goal:

- Produce user-facing, explainable area scores from tested components.

Core marts:

- `rpt_area_affordability`
- `rpt_area_commute`
- `rpt_area_safety_indicators`
- `rpt_area_energy_profile`
- `rpt_area_flood_planning_profile`
- `rpt_area_market_context`
- `rpt_neighbourhood_score`
- `rpt_tradeoff_explanations`

Example score components:

```text
affordability_score =
  score_rent_to_income
  + score_rent_vs_local_distribution
  + score_energy_cost_pressure

commute_score =
  score_commute_minutes
  + score_transport_access
  + score_commute_reliability_if_available

risk_score =
  score_flood_risk
  + score_planning_constraint_count
  + score_crime_indicator_rate

market_context_score =
  score_sale_price_trend
  + score_rent_growth
  + score_planning_supply_signal
```

Important:

- Store component scores and final score.
- Store human-readable explanation fragments.
- Store confidence and coverage fields.
- Let user weights change the final ranking without changing raw component facts.

Suggested TDD slices:

1. Affordability score changes when income and max rent change.
2. Missing data lowers confidence rather than producing a misleading zero.
3. Weighted ranking changes when the user prioritises commute over rent.
4. Every ranked area has at least one positive and one caution explanation where data supports it.
5. Final scores and component scores remain between 0 and 100.

Exit criteria:

- Every displayed score can be decomposed into source-backed components.
- Every area has a confidence/coverage indicator.
- Tests assert score bounds, non-null explanations, and no unsupported area ranks.

## Phase 5: Build The User-Facing App

Goal:

- Replace the current chart dashboard with a decision workflow.

Design direction:

- Subject: UK renters and movers making a high-stakes location decision under budget, commute, safety, energy, and risk constraints.
- Audience: students, new workers, migrants, families, and low-to-middle-income renters who need transparent trade-offs rather than glossy property listings.
- Page job: help the user shortlist areas and understand why those areas fit or fail.
- Visual tone: practical, calm, map-and-ledger inspired, with strong tabular comparison and restrained risk indicators.
- Signature element: a "trade-off receipt" for each area, showing affordability, commute, energy, safety indicators, flood/planning flags, confidence, and source freshness in one compact explainable panel.

Screens:

- Search and preferences.
- Ranked neighbourhoods.
- Compare 2-3 areas.
- "Why this area?" explanation panel.
- Map/table view.
- Listing checker for user-entered rent/listing details.
- Source and caveat page.

Minimum UI behaviour:

- User can set budget and income.
- User can enter destination postcode or coordinates.
- User can adjust commute, affordability, safety, energy, flood, and long-term-prospect weights.
- Ranking updates based on weights.
- User can compare areas side by side.
- User can see source freshness and caveats.

Web interface requirements:

- Form controls have visible labels, meaningful names, and suitable input types.
- URL reflects filters, selected area, comparison set, and weights.
- Keyboard focus states are visible.
- Icon-only controls have accessible names.
- Async loading and validation messages use polite live regions.
- Tables use tabular numerals and handle long place names without layout breakage.
- Empty states explain what to change next.
- Reduced-motion preferences are respected.
- Dates, currencies, and percentages use locale-aware formatting.
- No `transition: all`, no click-only divs, no disabled zoom, no unlabelled inputs.

Exit criteria:

- A non-technical user can answer "which areas should I consider first and why?"
- App does not require live listing scraping.
- App makes uncertainty visible.

## Phase 6: Testing And Quality Gates

Goal:

- Make the product credible, not just visually impressive.

Approach:

- Keep tests behaviour-facing. For example, test "user can rank areas by affordability and commute" through public functions or app-facing data, not private helper implementation.
- Use one tracer-bullet test before building each new subsystem.
- Request code review after each meaningful implementation phase and before merging.

Tests to add:

- Source availability and schema tests.
- Area join coverage tests.
- Score bounds tests.
- Explanation completeness tests.
- Dashboard DB smoke tests.
- Streamlit import or page smoke tests.
- Known-scenario tests, for example: high London budget vs low regional budget.
- UI guideline review for Streamlit pages or frontend files before release.

Quality gates:

- `dbt build`
- `sqlfluff lint`
- Python compile/import checks.
- Dashboard DB smoke test.
- Source freshness check. Done for the current repo's PR CI and docs workflow.
- UI accessibility/design guideline review.
- Optional stored app screenshots/demo assets if the UI becomes central to the portfolio. The CI browser smoke is already in place.

Exit criteria:

- CI catches broken data contracts and broken dashboard extracts.
- README claims match automated checks.

## Phase 7: Deployment

Goal:

- Deploy a public, reproducible MVP.

Recommended MVP deployment:

- Streamlit Community Cloud for the app.
- GitHub Pages for dbt docs.
- Committed slim `data/dashboard.duckdb` or release artifact for app data.
- Scheduled manual refresh at first; automated refresh later.

Later deployment:

- FastAPI backend if response logic outgrows Streamlit.
- Object storage for larger Parquet snapshots.
- GitHub Actions scheduled data refresh if licence and data size allow.

Exit criteria:

- Public app URL.
- Public dbt docs URL.
- README with setup, data caveats, screenshots, and architecture diagram.
- Workflow docs link to the exact GitHub Actions features used: workflow syntax, events, token permissions, caching/artifacts if added.

## Phase 8: Portfolio Positioning

Goal:

- Make the project read as mature product analytics and analytics engineering.

Portfolio story:

> I turned a tested public-data property warehouse into a renter-first neighbourhood decision-support tool. It combines official rent, sale, energy, crime, planning, flood, and transport signals into explainable area recommendations with confidence and source caveats.

What hiring managers should see:

- Multi-source data modelling.
- Geospatial joins.
- Tested dbt marts.
- Product judgement.
- Ethical caveats around sensitive indicators.
- A deployed app that solves a real user problem.

## Suggested Timeline

Two-week prototype:

- Harden existing repo.
- Add geography foundation.
- Add ONS rent and Land Registry market context.
- Build basic affordability ranking.
- Build first Streamlit decision workflow.

Six-week credible MVP:

- Add EPC, crime, flood/planning, and commute.
- Build explainable scoring.
- Add comparison view and source caveats.
- Add dashboard DB CI validation.
- Deploy app and docs.

Ten-week portfolio-grade product:

- Add better commute modelling.
- Add user-entered listing checker.
- Add area confidence and coverage dashboard.
- Add geospatial QA tests.
- Add screenshots, write-up, and short demo video.

## Review Checkpoints

Use code review checkpoints to keep the work honest:

- After Phase 1 hardening.
- After geography foundation.
- After the first two-source decision mart.
- After the scoring module.
- After the first usable UI workflow.
- Before public release.

Each review should check:

- Does the implementation match the plan?
- Are tests behaviour-facing?
- Are source caveats visible?
- Does CI prove the dashboard extract and dbt marts agree?
- Is the UI accessible and clear enough for a renter under pressure?
