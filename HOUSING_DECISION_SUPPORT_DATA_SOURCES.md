# Housing Decision Support Data Sources

Date checked: 2026-07-15

This file records the source provenance of the completed England-and-Wales reference implementation. The guiding rule is to use official/open data, avoid portal scraping, and label coverage, grain, and freshness without implying an active product roadmap.

## Active correctness-release sources (9)

| Source | Shipped use | Access | Grain | Caveats |
|---|---|---|---|---|
| HM Land Registry Price Paid Data | Sale prices, volume, market context | Public CSV/TXT | Transaction/postcode | England and Wales only; not live listings or a valuation |
| ONS Private Rent and House Price statistics | Official rent and affordability context | ONS downloads | Local authority | Provisional/revisable and coarser than neighbourhood grain |
| ONS Postcode Directory | Postcode to LSOA/MSOA/local authority/region | Official lookup download | Postcode | Snapshot provenance applies |
| ONS MSOA population estimates | Recorded-crime denominator | Official ONS workbook | MSOA 2021 | Mid-2024 resident estimate, not a live count |
| EPC data | Energy-efficiency indicator | GOV.UK bulk data | Certificate/postcode | Certificates may be expired or replaced |
| Police open data | Recorded-crime indicator | Public bulk/API data | Event/month | Indicator only; never a safe/unsafe verdict |
| Planning Data Platform | Planning-constraint coverage | Bulk geometry | Entity/geometry | England only; Wales is `not_covered` |
| Environment Agency flood-risk zones | Flood indicator, distributed through Planning Data Platform | Bulk geometry | Zone/postcode intersection | England-only area context, not property-level risk |
| OpenStreetMap | Amenities and station proximity | Geofabrik extract | Point/way/relation | Completeness follows OSM coverage |

Shipped geography decision:

- Rank MSOAs as the canonical indicator areas.
- Use full postcode as a user/listing lookup key, not as the final recommendation grain.
- Roll LSOA, postcode, EPC, crime, planning, flood, and local-authority evidence up into MSOA-level area profiles with explicit coverage and evidence-quality notes.

## Evaluated but not implemented

TfL journey planning, OpenTripPlanner/GTFS routing, live rental listings, portal scraping, and user-listing persistence were evaluated during discovery but are not built and have no active roadmap. The public listing check accepts user input for a one-off comparison; it does not ingest or store listing feeds.

## Active source details

Paths named below are implemented repository paths. Historical candidate model names have been removed so this catalogue does not imply unbuilt lineage.

### HM Land Registry Price Paid Data

URL: https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads

Relevant facts checked:

- The page was last updated on 1 June 2026.
- Data includes property sales in England and Wales lodged for registration.
- The page says the data is updated monthly, on the 20th working day.
- The complete file covers 1 January 1995 to the most current monthly data.
- The dataset is under the Open Government Licence v3.0, with extra attention needed for address data.

How to use:

- Keep it as market context, not renter market truth.
- Use sale-price trend, volume, property type mix, and new-build indicators.
- Refresh using full yearly or complete files with explicit source release metadata.

Implemented paths: `scripts/download_raw.py`, `scripts/load_to_duckdb.py`,
`stg_landreg__transactions`, `fct_transactions`, `int_area__market`, and
`rpt_area_profile_mvp`.

### ONS Private Rent And House Price Statistics

URL: https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/privaterentandhousepricesuk/latest

Relevant facts checked:

- Latest release checked was "Private rent and house prices, UK: June 2026", released 17 June 2026.
- ONS reported average UK monthly private rent of GBP 1,383 in May 2026.
- ONS reported London average rent of GBP 2,294 and North East average rent of GBP 776 in May 2026.
- ONS notes some values are provisional and subject to revision.
- ONS links to downloadable datasets for private rents and house prices.

How to use:

- Use as the official rent backbone.
- Publish the available local-authority grain explicitly.
- Use property size where available.
- Add a caveat that official rent statistics are not live listing prices.

Implemented paths: `scripts/prepare_ons_rent_seed.py`, `ref_ons_rent`,
`rpt_area_profile_mvp`, and `rpt_neighbourhood_score`.

### ONS / Geography Postcode Lookup

URL: https://geoportal.statistics.gov.uk/

How to use:

- Prepare a local lookup snapshot with `scripts/prepare_onspd_seed.py` from an official CSV/ZIP; keep the full upstream file out of git.
- Use the normalized output to populate the postcode-to-LSOA/MSOA/local-authority/region bridge.
- Treat the committed `ref_onspd_sample` seed as a CI fixture, not as production geography coverage.
- Stamp the source snapshot date, source name, and source URL onto every row.

Implemented paths: `scripts/prepare_onspd_seed.py`, `scripts/load_geography.py`,
`stg_geo__postcodes`, `dim_postcode_geography`, and `dim_area`.

### ONS MSOA Population Estimates

URL: https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/middlesuperoutputareamidyearpopulationestimatesnationalstatistics

Relevant facts checked:

- The accredited official-statistics workbook released 7 November 2025 contains mid-2024 estimates for 2021 MSOAs in England and Wales.
- The population reference date is 30 June 2024 and the source is licensed under the Open Government Licence.

How to use:

- Normalize the `Mid-2024 MSOA 2021` sheet with `scripts/prepare_msoa_population.py`.
- Use the committed 7,264-row seed as the compatible resident-population denominator for monthly recorded-crime rates.
- Expose the denominator, reference date, geography version, and source beside the rate.

Implemented paths: `scripts/prepare_msoa_population.py`,
`ref_msoa_population`, `rpt_area_profile_mvp`, and
`rpt_neighbourhood_score`.

### EPC Data

URL: https://get-energy-performance-data.communities.gov.uk/

Relevant facts checked:

- The service supports bulk certificate downloads and developer API access.
- It covers Energy Performance Certificates for domestic properties.
- It covers England and Wales.
- Data includes certificates registered since 2012, which may have expired or been replaced.
- Bulk access requires GOV.UK One Login.

How to use:

- Aggregate EPC ratings by postcode/outcode/LSOA/MSOA/local authority.
- Estimate energy-cost pressure with caveats.
- Track certificate recency and replacement status where possible.

Implemented paths: `scripts/prepare_epc_seed.py`, `scripts/load_epc.py`,
`stg_epc__certificates`, `int_area__energy`, and `rpt_area_profile_mvp`.

### Police API

URL: https://data.police.uk/docs/

Relevant facts checked:

- The API provides street-level crime and outcome data.
- It uses JSON web service endpoints over HTTP GET and POST.
- It includes crime-related and neighbourhood-related methods.

How to use:

- Aggregate monthly crime categories around area centroids or within area boundaries.
- Convert counts into monthly rates using the compatible ONS mid-2024 MSOA population denominator.
- Do not call areas "safe" or "unsafe"; show indicator levels and uncertainty.

Implemented paths: `scripts/prepare_crime_seed.py`, `scripts/load_crime.py`,
`stg_crime__street`, `int_area__crime`, and `rpt_area_profile_mvp`.

### Planning Data API

URL: https://www.planning.data.gov.uk/docs

Relevant facts checked:

- The Planning Data API gives access to over 100 planning and housing datasets for England.
- It supports coordinate, UPRN, dataset, geometry, and pagination parameters.
- It has datasets such as conservation areas, listed buildings, green belt, flood-risk-zone, Article 4 direction areas, tree preservation zones, brownfield land, and planning applications.
- The documentation says planning application data specification is in development and local planning authorities are not currently required to share application data to that specification.
- Bulk downloads are available as CSV, JSON, GeoJSON, and where applicable Parquet.

How to use:

- Start with planning constraints and designations.
- Use bulk downloads for stable snapshots and local spatial joins.
- Mark Wales `not_covered`; never turn unsupported coverage into a zero constraint count or low flood flag.

Implemented paths: `scripts/prepare_area_constraints.py`,
`scripts/load_constraints.py`, `stg_constraints__area`, and
`rpt_area_profile_mvp`.

### Environment Agency Flood-Risk Zones

URL: https://environment.data.gov.uk/

The shipped input is static England flood-risk-zone geometry distributed through
the Planning Data Platform, not the live flood-monitoring API. Postcode
intersections are rolled up to MSOA and published as area context only. Wales is
`not_covered`; the output is not a property-level survey or prediction.

Implemented paths: `scripts/prepare_area_constraints.py`,
`scripts/load_constraints.py`, `stg_constraints__area`, and
`rpt_area_profile_mvp`.

### Transport / Commute

**Status: evaluated, not implemented, and not on an active roadmap.** The notes
below record why this source was not included; none of the candidate model names
from discovery are part of the repository contract.

TfL URL: https://api-portal.tfl.gov.uk/

Relevant facts checked:

- TfL recommends registering for the Unified API.
- API requests use an `app_key` query parameter.
- TfL public open data can be used subject to transport data terms and conditions.

The shipped convenience indicator uses OpenStreetMap station proximity and makes
no commute-time claim.

### OpenStreetMap / Overpass

URL: https://wiki.openstreetmap.org/wiki/Overpass_API

Relevant facts checked:

- Overpass is a read-only API for querying OpenStreetMap data.
- Public instance usage policies matter, especially for larger refreshes.
- The wiki notes a general safe-use assumption on the main public instance for fewer than 10,000 queries per day and less than 1 GB downloaded per day, with identifying headers.

How to use:

- Use for amenities: supermarkets, parks, schools, gyms, libraries, rail stations, bus stops, pharmacies.
- For larger area refreshes, use extracts rather than hitting public APIs repeatedly.

Implemented paths: `scripts/prepare_amenity_access.py`,
`scripts/load_amenities.py`, `stg_amenities__area`, and
`rpt_area_profile_mvp`.

## Data Model Notes

The implemented decision path is:

```text
stg_landreg__transactions ─┐
stg_geo__postcodes ────────┤
stg_epc__certificates ─────┤
stg_crime__street ─────────┤
stg_constraints__area ─────┼─> rpt_area_profile_mvp ─> rpt_neighbourhood_score
stg_amenities__area ───────┤
ref_ons_rent ──────────────┤
ref_msoa_population ───────┘
```

The core spine is `dim_postcode_geography` plus `dim_area`; Land Registry
transactions also feed the established core/analytics marts. There are no
transport-node, commute, user-listing, or separate safety-verdict marts.

## Minimum Data Quality Tests

For every source:

- Required columns are present.
- Source row count is within expected bounds.
- Source release date is captured.
- Load timestamp is captured.
- Licence/caveat metadata exists.

For geography:

- No duplicate area IDs.
- Coordinates are within UK bounds.
- Postcode to area coverage meets a chosen threshold.
- Unmapped records are counted and exposed.

For scoring:

- All component scores are within 0 to 100.
- Final scores are within 0 to 100.
- Scores have explanation text.
- Scores have source coverage and evidence-quality fields.
- Missing or unsupported data lowers evidence quality rather than silently becoming zero.

## Current preparation paths

The real-source build prepares geography, ONS rent, Land Registry, EPC, police
records, ONS MSOA population, planning/flood geometry, and OpenStreetMap
amenities with the `scripts/prepare_*` / `scripts/load_*` commands documented in
the root README. Fixture CI selects the committed source seeds. A one-off user
listing comparison is an API calculation over these area facts, not a tenth
ingested source.
