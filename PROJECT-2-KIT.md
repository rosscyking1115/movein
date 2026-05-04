# Project 2 — UK Public Data Analytics with dbt + DuckDB

> Two-week sprint. Ship a public, recruiter-credible analytics-engineering
> project that closes the SQL/dbt gap on Ross's CV and unlocks Data Analyst,
> Data Engineer, and Analytics Engineer roles for autumn 2026.
>
> Drop this file into a fresh chat with a coding-capable model (filesystem +
> shell tools required). Paste the kickoff prompt in §1 and the model can
> drive the build phase by phase.

---

## 0. Why this project exists

The portfolio has strong ML / NLP / PySpark signals already. What it's missing
— and what every UK data role tests for — is the analytics-engineering
spine: clean SQL, dbt models, tests, documentation, lineage, a lightweight
warehouse, and a dashboard. One repo closes that gap.

**Success looks like a repo that:**

1. Ingests a real, named UK public dataset.
2. Has 15–20 dbt models across `staging → intermediate → marts`.
3. Tests every mart (≥ 1 generic + ≥ 1 custom test per mart).
4. Renders dbt docs with full column-level lineage on GitHub Pages.
5. Powers a deployed dashboard answering 5–7 named business questions.
6. Builds and tests automatically on every PR (GitHub Actions, green badge).
7. Has a README a hiring manager understands in 90 seconds.

**Time budget: ~14 working days (or ~28 evenings)**. Each phase below has a
day-count. Treat them as upper bounds — most will go faster.

---

## 1. Kickoff prompt for the new chat

````
We're building a UK analytics-engineering portfolio project following
PROJECT-2-KIT.md. Stack: dbt + DuckDB + Streamlit (or Evidence) + GitHub
Actions. Two-week sprint, nine phases.

Ground rules:
- Every model needs a description and at least one test.
- Naming: `stg_<source>__<entity>`, `int_<purpose>`, `dim_<entity>`,
  `fct_<event>`. Plural never.
- One PR per phase. CI must be green before merge.
- Use heredocs for any file write longer than ~60 lines, then verify with
  `wc -l`. Don't use the Write tool for SQL — it has truncated mid-CTE
  before.
- After each phase: `dbt build`, `dbt docs generate`, commit with a
  conventional-commits message, push, open PR.
- Treat §10 (Lessons learned) as a pre-flight checklist.

Start by walking me through dataset selection (§3) — ask which of the four
candidates I want, and confirm I have the prerequisites in §4. Then begin
Phase 0.
````

---

## 2. Stack at a glance

| Layer | Tool | Why |
| --- | --- | --- |
| Warehouse | **DuckDB** | Free, fast, single-file, runs in CI |
| Transform | **dbt-core 1.8+ with `dbt-duckdb`** | Standard analytics-engineering tool |
| SQL lint | **sqlfluff** + dbt template | Catches style + bug-class issues |
| Tests | dbt generic + `dbt-expectations` + custom singular tests | Three test layers |
| Docs | `dbt docs` deployed to GitHub Pages | Free hosting, lineage graph |
| Dashboard | **Streamlit** *or* **Evidence** | Streamlit = Python, Evidence = SQL+Markdown |
| CI | GitHub Actions | Build + test on every PR |
| Pre-commit | `pre-commit` framework | sqlfluff + dbt-checkpoint |
| Python | 3.11+ via `uv` or `venv` | dbt-duckdb's compat sweet spot |

Pin everything in `requirements.txt` (or `pyproject.toml`). Do **not** use
the latest dbt 1.9 yet — 1.8 has the broadest adapter coverage and is what
most UK shops still run.

---

## 3. Dataset selection

Pick one from this list. The kit is written so any of the four works; the
choice mainly affects narrative and which roles the project speaks to.

### Selection criteria (use these to decide)

- **Story:** can a hiring manager grasp the "so what" in one sentence?
- **Size:** big enough to be non-trivial (≥ 1M rows), small enough that
  DuckDB handles it on a laptop (< 5 GB).
- **Modelability:** does it factor into clean dimensions + facts, or is it
  one flat table?
- **Refresh:** is there a rolling update (monthly/weekly) so the project
  stays alive after launch?

### Candidate A — **HM Land Registry Price Paid Data** ⭐ recommended

- **Source:** [GOV.UK Price Paid](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads)
- **Size:** ~30M rows since 1995, monthly updates, ~5 GB CSV (~1.5 GB Parquet).
- **Story:** "Where in England & Wales is housing actually affordable in
  2026?" or "How did the post-COVID commute corridor reshape London prices?"
- **Modelling:** transactions (fact) × property (dim) × postcode (dim) ×
  date (dim) × buyer-type (dim) × price-band (dim). Six clean dimensions.
- **Audience:** every UK data role gets it; doubles as a finance/property
  story for fintechs (Wise, Zoopla, Rightmove signals).
- **Caveat:** wide enough to fill 14 days; resist scope creep.

### Candidate B — **TfL Cycle Hire**

- **Source:** [TfL open data](https://cycling.data.tfl.gov.uk/)
- **Size:** ~100M trips since 2012, weekly CSVs.
- **Story:** "Has Santander Cycles recovered post-COVID, and which docking
  stations are the new winners?"
- **Modelling:** trip (fact) × station (dim) × date (dim) × weather (dim,
  joinable from Met Office) × bike-type (dim).
- **Audience:** consumer-tech (Just Eat, Trainline, Deliveroo), TfL itself.

### Candidate C — **NHS A&E Attendances and Emergency Admissions**

- **Source:** [NHS England statistical works](https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/)
- **Size:** ~3M rows, monthly, by trust.
- **Story:** "Which trusts are quietly missing the four-hour target — and
  is the 2024 winter performance reverting to the 2019 baseline?"
- **Modelling:** attendance (fact) × trust (dim) × date (dim) × type (dim).
- **Audience:** healthtech (Babylon's successor cohort, Cera, AccuRx,
  Smart Communications), public sector (Faculty's NHS work).
- **Caveat:** sensitive subject — keep tone analytical, not editorial.

### Candidate D — **Premier League event data (FBref / StatsBomb open)**

- **Source:** FBref scrapes or StatsBomb open data.
- **Size:** ~2M events per season × 5–10 seasons.
- **Story:** "Which Premier League teams over- or under-performed their xG
  in 2025/26?"
- **Modelling:** event (fact) × player (dim) × team (dim) × match (dim)
  × competition (dim).
- **Audience:** sports-tech, betting (Entain, Flutter, bet365), media
  (Sky, BBC).
- **Caveat:** only relevant if Ross likes football; recruiters can tell
  when the dataset choice is performative.

> **Recommendation:** Land Registry. Strongest narrative-to-effort ratio
> for a UK data role and survives the "tell me about a real-world impact"
> interview question without needing domain expertise.

---

## 4. Prerequisites (do before Phase 0)

- Python ≥ 3.11. Recommend `uv` (faster) or stdlib `venv`.
- Git ≥ 2.40, GitHub account.
- A new repo name (e.g., `uk-property-analytics`).
- ~5 GB free disk for the warehouse + raw downloads.
- (Optional but recommended) Streamlit Cloud account *or* Vercel — for
  dashboard hosting.

```bash
python -m venv .venv
source .venv/bin/activate            # macOS/Linux
# .venv\Scripts\activate             # Windows PowerShell
pip install -U pip uv
uv pip install dbt-core==1.8.* dbt-duckdb sqlfluff sqlfluff-templater-dbt \
               pre-commit duckdb pandas pyarrow streamlit
```

Save to `requirements.txt`:

```bash
uv pip freeze > requirements.txt
```

---

## 5. Repo layout (target)

```
uk-property-analytics/
├─ .github/
│  └─ workflows/
│     ├─ ci.yml                  # dbt build + test + sqlfluff
│     └─ docs.yml                # publish dbt docs to GH Pages
├─ .pre-commit-config.yaml
├─ .sqlfluff
├─ .sqlfluffignore
├─ profiles.yml.example          # never commit profiles.yml itself
├─ dbt_project.yml
├─ packages.yml
├─ requirements.txt
├─ README.md
├─ data/                         # raw + intermediate downloads (gitignored)
├─ scripts/
│  ├─ download_raw.py            # pulls latest data
│  └─ load_to_duckdb.py          # CSV/Parquet → DuckDB raw schema
├─ models/
│  ├─ staging/
│  │  ├─ _sources.yml
│  │  ├─ _models.yml
│  │  └─ stg_landreg__transactions.sql
│  ├─ intermediate/
│  │  └─ int_transactions__enriched.sql
│  └─ marts/
│     ├─ core/
│     │  ├─ dim_postcode.sql
│     │  ├─ dim_property_type.sql
│     │  ├─ dim_date.sql
│     │  └─ fct_transactions.sql
│     └─ analytics/
│        ├─ rpt_price_per_sqm_by_region.sql
│        └─ rpt_yoy_change_by_region.sql
├─ tests/                        # singular SQL tests
│  └─ assert_no_negative_prices.sql
├─ macros/
│  └─ generate_schema_name.sql
├─ snapshots/                    # SCD2 if needed
├─ analyses/                     # ad-hoc analytical SQL (not built)
├─ seeds/
│  └─ ref_region_lookup.csv
├─ docs/                         # built dbt docs site (gitignored)
└─ dashboard/
   ├─ streamlit_app.py
   └─ pages/
      ├─ 1_market_overview.py
      └─ 2_regional_deepdive.py
```

---

## 6. The nine phases

Each phase ends with a green CI run and a merged PR. Don't move on until
the previous phase is on `main`.

### Phase 0 — Bootstrap (Day 1, ~3 hours)

```bash
mkdir uk-property-analytics && cd uk-property-analytics
git init
python -m venv .venv && source .venv/bin/activate
uv pip install dbt-core==1.8.* dbt-duckdb sqlfluff sqlfluff-templater-dbt pre-commit
uv pip freeze > requirements.txt
dbt init analytics --skip-profile-setup    # creates skeleton in ./analytics/
# Move generated files up one level so the repo root IS the dbt project
```

- Create `profiles.yml.example` with a DuckDB profile pointing at
  `./data/warehouse.duckdb`. **Add `profiles.yml` to `.gitignore`.**
- Create `.sqlfluff` (templater = dbt, dialect = duckdb, max_line_length = 100).
- Add `.gitignore` covering `data/`, `*.duckdb`, `target/`, `dbt_packages/`,
  `logs/`, `.venv/`, `profiles.yml`, `docs/`.
- Write a 5-line README with the project pitch.
- Push to GitHub. Enable branch protection on `main`: require PR + status
  checks (we'll add the check name in Phase 7).

**Exit check:** `dbt debug` connects to DuckDB; `dbt run` (with no models)
exits 0; the empty repo is on GitHub.

### Phase 1 — Raw ingestion (Day 2, ~4 hours)

```bash
# scripts/download_raw.py — idempotent download of the year's CSV(s)
# scripts/load_to_duckdb.py — read CSV with pandas/pyarrow, write to
#   a `raw` schema in DuckDB, add a `_loaded_at` timestamp column.
```

- Define a `raw_landreg.transactions` table. Use Parquet on disk for speed.
- Document column meanings in `README.md` (link to the GOV.UK data dictionary).
- Add `_sources.yml` declaring the raw table with column descriptions and
  a freshness check (`warn_after: { count: 35, period: day }`).

**Exit check:** `duckdb data/warehouse.duckdb 'select count(*) from raw_landreg.transactions'`
returns the expected row count; `dbt source freshness` is green.

### Phase 2 — Staging models (Days 3–4, ~8 hours)

One staging model per source table. The staging layer's job is **type
casting + renaming + light cleanup — no business logic**.

```sql
-- models/staging/stg_landreg__transactions.sql
with source as (
    select * from {{ source('landreg', 'transactions') }}
),
renamed as (
    select
        transaction_id::varchar                         as transaction_id,
        price::bigint                                   as price_gbp,
        cast(date_of_transfer as date)                  as transferred_on,
        upper(trim(postcode))                           as postcode,
        nullif(property_type, '')                       as property_type_code,
        nullif(old_new, '')                             as is_new_build_flag,
        nullif(duration, '')                            as tenure_code,
        nullif(paon, '')                                as primary_address,
        nullif(saon, '')                                as secondary_address,
        nullif(street, '')                              as street,
        nullif(locality, '')                            as locality,
        nullif(town_city, '')                           as town_city,
        nullif(district, '')                            as district,
        nullif(county, '')                              as county,
        case ppd_category_type
            when 'A' then 'standard'
            when 'B' then 'additional'
        end                                              as ppd_category,
        record_status_code                               as record_status_code,
        _loaded_at
    from source
    where price > 0                  -- guard against historic data junk
)
select * from renamed
```

- Add `_models.yml` documenting every column with a description and at
  least one test. Required tests: `not_null` on PK, `unique` on PK,
  `accepted_values` on enums.
- Run `dbt build --select staging` — must pass.

**Exit check:** all staging models build, all tests pass, `dbt docs generate`
shows descriptions on every column.

### Phase 3 — Intermediate + marts (Days 5–7, ~14 hours)

This is the core of the project. Aim for **8–12 models here**.

**Intermediate** (one or two models): join staging tables, derive computed
columns. Examples:
- `int_transactions__enriched` — join transactions with the postcode
  region lookup (a seed file you can populate from ONS open data).

**Dimensions** (3–4 models, prefix `dim_`):
- `dim_date` — a generated calendar (use the `dbt_date` package).
- `dim_postcode` — postcode → outward code → region → country.
- `dim_property_type` — code → human label.
- `dim_tenure` — freehold / leasehold.

**Facts** (1–2 models, prefix `fct_`):
- `fct_transactions` — one row per sale. Surrogate key, FKs to every dim,
  measures: `price_gbp`, `price_per_sqm` (if you can join sqm — you can't
  from Land Registry alone, so leave it out and document why).

**Reporting / mart-analytics layer** (3–4 models, prefix `rpt_`):
- `rpt_price_yoy_by_region` — annual % change by region.
- `rpt_top_postcodes_by_volume` — busiest postcodes by year.
- `rpt_new_build_premium` — new-build vs existing premium over time.

For each mart: declare the **grain** in the model description (one row per
X per Y) — interviewers love this.

**Exit check:** `dbt build --select marts` — all green; `dbt docs serve`
shows a clean lineage graph from sources → marts.

### Phase 4 — Tests + data quality (Day 8, ~5 hours)

Two layers of tests:

1. **Generic tests** in `*.yml` — `not_null`, `unique`, `relationships`,
   `accepted_values`. Already added in Phases 2–3; audit and extend.
2. **Singular tests** in `tests/` — SQL files that return failing rows.
   Examples:
   - `assert_no_negative_prices.sql` — `select * from fct_transactions where price_gbp <= 0`
   - `assert_postcodes_match_region_lookup.sql` — orphan postcodes.
   - `assert_no_future_transactions.sql` — date sanity.

Add `dbt-expectations` package for column-level distribution tests:

```yaml
# packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
  - package: calogica/dbt_expectations
    version: 0.10.4
  - package: calogica/dbt_date
    version: 0.10.1
```

Then `dbt deps && dbt build`.

**Exit check:** every mart has ≥ 1 generic + ≥ 1 custom test. Total tests
≥ 30. `dbt test` returns green.

### Phase 5 — Documentation + lineage (Day 9, ~4 hours)

- Backfill any missing column descriptions.
- Add a `dbt_project.yml` description per model folder.
- Generate docs locally: `dbt docs generate && dbt docs serve` — sanity
  check the lineage.
- Set up `.github/workflows/docs.yml` to publish `target/` to GitHub Pages
  on every push to `main`.
- Write the proper README:
  - Pitch (one paragraph).
  - Architecture diagram (mermaid — sources → staging → int → marts).
  - Business questions answered (5–7).
  - How to run (3 commands).
  - Tech choices and why.
  - Link to live docs site, live dashboard, CI.

**Exit check:** GH Pages shows the live docs site; the README's "How to
run" reproduces a clean build from a fresh clone.

### Phase 6 — Dashboard / consumption (Days 10–11, ~10 hours)

Pick one and commit:

- **Streamlit** — Python-native, easiest if you want logic in pandas.
  Deploy to Streamlit Community Cloud (free).
- **Evidence** — SQL + Markdown, beautiful by default. Deploy to Vercel.

Either way:

- 5–7 charts, each tied to a named business question.
- Connect to DuckDB read-only (Streamlit: `duckdb.connect(read_only=True)`).
- Each chart caption links back to the dbt model that powers it.
- One-page "About" tab explaining the project + linking back to GitHub.

**Exit check:** dashboard is on a public URL; every chart loads in < 2s
on a cold start; mobile layout is at least usable.

### Phase 7 — CI/CD + polish (Days 12–13, ~6 hours)

`.github/workflows/ci.yml`:

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]
jobs:
  build:
    name: dbt build + test          # ← exact display name; use in branch protection
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: dbt deps
      - run: python scripts/download_raw.py --sample      # tiny CI dataset
      - run: python scripts/load_to_duckdb.py
      - run: dbt build --target ci
      - run: sqlfluff lint models/ --dialect duckdb --templater dbt
```

- Add a `--sample` flag to `download_raw.py` that pulls only the latest
  month, so CI runs in < 90 seconds.
- Add a `target: ci` profile in `profiles.yml.example` that uses an
  in-memory DuckDB.
- Wire `pre-commit` so sqlfluff runs on staged SQL.
- README badges: CI status, model count, test count.

**Branch protection (GitHub → Settings → Branches → main):** require the
display name `dbt build + test`. **Not** the workflow file name `CI`.

**Exit check:** open a PR — CI runs green in < 2 minutes; merge is blocked
until CI is green.

### Phase 8 — Writeup + portfolio integration (Day 14, ~4 hours)

- Write a project page on the portfolio site (`content/projects/uk-property-analytics.mdx`):
  - Summary (≤ 140 chars).
  - Architecture diagram embedded.
  - 3–5 paragraphs: problem, approach, what broke, what's next.
  - Links: GitHub repo, live docs, live dashboard.
  - Cover image (1200×630) — screenshot of the dashboard.
- Pin the GitHub repo to your profile.
- Post on LinkedIn with the dashboard screenshot + 3-bullet summary +
  links. Tag `#dbt #analyticsengineering #ukjobs`.
- Add a one-liner to your CV under "Projects" pointing at the live URL.

**Exit check:** project shows up on the portfolio site at
`/projects/uk-property-analytics`; LinkedIn post is live; CV updated.

---

## 7. Interview-ready talking points to bake in

These are the questions that come up in every analytics-engineering
interview. Make sure your repo answers each one *before* you ship.

| Question | Where the repo answers it |
| --- | --- |
| "Walk me through a model you're proud of." | Pick `fct_transactions` or one rpt mart; document the grain explicitly |
| "How do you handle data quality?" | Phase 4 — three layers of tests, screenshot the test count |
| "What does your lineage look like?" | dbt docs site (Phase 5) — drop the link |
| "How do you test in CI?" | `.github/workflows/ci.yml` (Phase 7) — small sample, full build |
| "What would you do differently next time?" | Add a `## Lessons` section to the README — humility scores |
| "How would you scale this beyond DuckDB?" | One paragraph in README on Snowflake/BigQuery migration path |

---

## 8. Acceptance criteria (the definition of done)

Tick every box on the live deploy:

- [ ] Repo is public on GitHub with README, license, branch protection.
- [ ] `git clone && pip install -r requirements.txt && python scripts/download_raw.py --sample && python scripts/load_to_duckdb.py && dbt build` succeeds in < 5 min on a clean machine.
- [ ] ≥ 15 dbt models split staging / intermediate / marts.
- [ ] ≥ 30 dbt tests, all green.
- [ ] dbt docs site live on GitHub Pages with full lineage.
- [ ] Streamlit / Evidence dashboard live, answering 5–7 business questions.
- [ ] CI green badge on README.
- [ ] sqlfluff zero violations on `dbt build --warn-error`.
- [ ] Branch protection requires the CI display name.
- [ ] Pre-commit installed and runs locally.
- [ ] Portfolio site has the project page, with cover image + live URLs.
- [ ] LinkedIn post is up.
- [ ] CV updated with the project link.

---

## 9. Day-to-day rhythm

| Day | Focus | PR opens? |
| --- | --- | --- |
| 1 | Phase 0 — bootstrap | Yes |
| 2 | Phase 1 — raw ingestion | Yes |
| 3–4 | Phase 2 — staging models | Yes |
| 5–7 | Phase 3 — intermediate + marts | Yes (one PR per layer is fine) |
| 8 | Phase 4 — tests | Yes |
| 9 | Phase 5 — docs | Yes |
| 10–11 | Phase 6 — dashboard | Yes |
| 12–13 | Phase 7 — CI/CD | Yes |
| 14 | Phase 8 — writeup + ship | Final PR + post |

Slip allowance: 2 buffer days. Use them on Phase 3 (it's the longest) or
Phase 6 (it's the most fiddly). Don't slip on Phase 4 — tests are what
make this CV-worthy.

---

## 10. Lessons learned + pre-flight checklist

These are the things that bite analytics-engineering projects. Re-read
this list before each phase.

### L1 — Never commit `profiles.yml`

It contains paths and (with other warehouses) credentials. Commit
`profiles.yml.example` and add the real one to `.gitignore`. CI uses
environment variables to populate the profile.

### L2 — Pin every package version

`dbt-core`, `dbt-duckdb`, every package in `packages.yml`. Floating
versions break six months later when you re-clone for an interview demo.

### L3 — `dbt-duckdb` adapter version must match `dbt-core` minor

`dbt-core 1.8.x` ↔ `dbt-duckdb 1.8.x`. Mixing minors causes silent macro
weirdness.

### L4 — DuckDB write-locks on Windows

Only one process can hold the warehouse file open in write mode. If a
Streamlit dev server is connected, `dbt run` will fail. Connect Streamlit
in `read_only=True` mode and you'll never see this.

### L5 — CSV parsing is slow; convert to Parquet once

The 30M-row Land Registry CSV takes ~90s to parse on every load if you
read it raw. Convert to Parquet once in `load_to_duckdb.py` and reload
from Parquet thereafter (~2s).

### L6 — Don't skip `dim_date`

Hand-rolled date logic in marts gets messy. Use `dbt_date.get_date_dimension`
to generate a 50-year calendar, join everywhere. Saves ~30 lines per mart.

### L7 — `relationships` tests need both sides materialised

A common trip: writing a `relationships` test from `fct_transactions` to
`dim_postcode` before `dim_postcode` is built in the same `dbt build`
invocation. dbt usually orders correctly via `ref()`, but if you ever
run `dbt test` standalone, materialise dims first.

### L8 — `unique` test on a fact table is rarely what you want

A fact table's "unique" key is usually a surrogate hash of multiple
columns. Use `dbt_utils.generate_surrogate_key` and test uniqueness on
the hash, not on a natural-looking column.

### L9 — sqlfluff + dbt templater = slow first run

First lint takes 30+ seconds while it compiles every model. Subsequent
runs are fast. Don't conclude it's broken after 20 seconds.

### L10 — Branch-protection check name

GitHub uses the **`name:` field** of the job, not the workflow file name
or the job ID. In this kit's `ci.yml` the name is `dbt build + test` —
type that exactly into branch protection.

### L11 — Streamlit Cloud has a 1 GB memory cap

A naive `pd.read_sql('select * from fct_transactions')` will OOM. Push
aggregation into DuckDB (`select region, sum(price) ...`) and only pull
display-sized result sets back to Python.

### L12 — DuckDB on Streamlit Cloud needs to be in the repo

Streamlit Cloud doesn't run `dbt build` for you. Either build the
warehouse in CI and commit a small filtered version (≤ 100 MB) for the
dashboard, or have the Streamlit app rebuild from a public Parquet on
S3 / R2 on cold start.

### L13 — `git lfs` for the warehouse, or don't commit it

If the `.duckdb` file is over GitHub's 100 MB hard limit, either filter
to a smaller analytical subset or use Git LFS. Don't try to force-push
a 500 MB binary — you'll lose 30 minutes.

### L14 — Mermaid diagrams in GitHub READMEs render natively

No need for an SVG. Inline ` ```mermaid ` fenced blocks render. For the
architecture diagram, mermaid > screenshot every time.

### L15 — Don't gold-plate the dashboard before Phase 6

It's tempting to start styling on day 1. The dashboard is downstream of
the data — if your marts change, your charts change. Build marts first,
chart last.

### L16 — Land Registry's data dictionary is your bible

Its CSV columns have non-obvious codes (`property_type=F` is "flat",
not "freehold"; `duration=F` *is* "freehold"). Read the dictionary
before writing the staging cast.

### L17 — Test the README's "how to run" on a fresh clone

Before declaring done, clone the repo into a temp folder you've never
worked in, follow the README literally, and time how long until you see
the dashboard. If it's > 10 minutes, the README is wrong.

---

## 11. Reproducibility checklist (before declaring "shipped")

- [ ] Cold clone + `pip install` + `dbt build` works on a clean machine.
- [ ] Cold clone + `streamlit run` works without manual setup beyond the README.
- [ ] CI runs green on a PR within 2 minutes.
- [ ] dbt docs site is live and lineage renders.
- [ ] Dashboard URL works on mobile.
- [ ] All 5–7 business-question answers are linkable (per-page URLs).
- [ ] License file present (MIT or Apache 2.0).
- [ ] LinkedIn post screenshot reads well at 1200×630.
- [ ] Recruiter-readable in 90 seconds: open the README, do they get it?

---

## 12. Things deliberately deferred

Don't add these in v1. Note them as "future work" in the README so the
absence is intentional, not an oversight.

- **Snowflake / BigQuery / Databricks adapter.** DuckDB tells the same
  story for free; document the migration path in 1 paragraph.
- **Airflow / Dagster / Prefect orchestration.** GitHub Actions cron is
  enough for a portfolio. If they ask, say "I'd reach for Dagster
  because asset-based modelling fits dbt naturally."
- **Looker / Hex / Mode.** Streamlit / Evidence ship faster and are
  free to host.
- **Great Expectations alongside dbt-expectations.** Pick one (we picked
  dbt-expectations).
- **Spark.** You already have Spark on the CV from the MSc work. Adding
  it here would be a flag, not a strength.
- **Real-time / streaming.** Out of scope for batch analytics.

---

## 13. Hand-off prompt for the next session (after launch)

When you come back to maintain this in 3 months:

````
I'm picking up the UK property analytics project. PROJECT-2-KIT.md is
the build plan; the live state is on `main`. Read the README, then
section 10 of the kit (lessons learned), then ask me what change I need.

For any change:
1. Branch off main.
2. Modify models / tests / dashboard.
3. Run `dbt build` locally.
4. Push, open PR — CI must be green before merge.
5. Update README and the portfolio MDX page if the change is user-visible.
````

---

*End of kit. Two-week sprint. One repo. Closes the SQL/dbt gap on the CV
and reads as a real analytics-engineering portfolio piece for every UK
data role on the shortlist.*
