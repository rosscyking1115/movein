"""About — project description, tech stack, links."""

import streamlit as st

st.set_page_config(page_title="About", page_icon="📊", layout="wide")

st.title("📊 About this project")

st.markdown(
    """
**uk-property-analytics** is an analytics-engineering portfolio piece — a
5-year UK housing market study built on HM Land Registry Price Paid data
(every recorded property transaction in England & Wales, 2021–2025).

The dashboard you're looking at is the *consumption layer* over a six-stage
pipeline: source → staging → intermediate → marts/core (dimensions + fact)
→ marts/analytics (reporting) → Streamlit. Every layer is tested
(91 tests across three layers), every column is documented (95 columns,
zero missing description), and the lineage graph is published to GitHub
Pages.

### Live links

- 📊 [**Live dbt docs (lineage + column catalogue)**](https://rosscyking1115.github.io/uk-property-analytics/)
- 💻 [**GitHub repo**](https://github.com/rosscyking1115/uk-property-analytics)

### Tech stack

| Layer | Tool |
|---|---|
| Warehouse | DuckDB |
| Transform | dbt-core 1.11 + dbt-duckdb 1.10 |
| Tests | built-in + dbt-utils + dbt-expectations + singular tests |
| Docs | dbt docs → GitHub Pages |
| Dashboard | Streamlit + Plotly |
| Source | HM Land Registry Price Paid (Open Government Licence v3.0) |

### Three things worth knowing

1. **The fact filters to `ppd_category='standard'`** (4.18M of 4.99M total
   rows). The excluded 16% are repossessions, BTL portfolio transfers,
   charity transfers, and corrections — real but not arm's-length market
   activity. Filter applied once in the int_ layer; every downstream mart
   inherits the discipline.
2. **The 'Unknown' region row in `dim_postcode`** (~2K rows) catches
   postcodes that don't match the 104-row `ref_postcode_area_region` seed
   — usually rare historic records with no postcode at all. The
   distinct-values-to-contain-set test guarantees the 10 ONS regions are
   present without rejecting Unknown as an extra value.
3. **Every reporting mart has a singular test** asserting a named risk
   hypothesis (e.g. *yoy %% within ±50%*, *premium %% within −50% to
   +250%*, *no future-dated transactions*). When asked "how do you think
   about data quality?" the answer is the eight `tests/assert_*.sql`
   files plus 73 generic tests plus 10 distribution tests across three
   layers.

### Source attribution

Contains HM Land Registry data © Crown copyright and database right.
Used under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
"""
)
