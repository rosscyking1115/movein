# Housing Decision Support Data Sources

Date checked: 2026-06-25

This file lists the practical sources for the UK housing decision-support product. The guiding rule is to use official/open data first, avoid portal scraping, and clearly label source coverage and freshness.

## Source Summary

| Source | Use | Access | Grain | MVP Priority | Caveats |
|---|---|---|---|---|---|
| HM Land Registry Price Paid Data | Sale prices, volume, market context | Public CSV/TXT/linked data | Transaction/postcode | High | England and Wales only; not live listings; address-data use has restrictions |
| ONS Private Rent and House Price statistics | Official rent levels and inflation | ONS datasets and bulletin downloads | Country, region, local authority, BRMA depending table | High | Latest values can be provisional and revised |
| ONS/geography postcode lookup | Postcode to LSOA/MSOA/local authority/region | Official geography lookup downloads | Postcode | High | Must check licensing and update cadence |
| EPC data | Energy efficiency and likely energy-cost pressure | GOV.UK service, bulk CSV, developer API | Property/certificate/postcode | High | Requires GOV.UK One Login for bulk; certificates may be expired or replaced |
| Police API | Crime indicator profile | Public JSON API | Street/lat-lon/neighbourhood/month | High | Avoid "safe/unsafe" labels; use rates and caveats |
| Planning Data API | Planning constraints, designations, applications, brownfield, flood-risk-zone | Public API and bulk downloads | Entity/geometry | Medium-high | Beta service; planning applications spec may change |
| Environment Agency flood monitoring / flood areas | Flood alerts/warnings and flood area polygons | Public API / spatial data | Flood area/geometry | Medium | Monitoring is real-time alert-oriented; long-term risk needs separate risk datasets |
| TfL Unified API | London commute estimates and transport access | API key recommended | Stop/journey/location | Medium | London-first; terms and quotas apply |
| OpenStreetMap / Overpass | Amenities, stations, green space, shops | Public OSM query APIs or extracts | Point/way/relation | Medium | Respect usage policies; use extracts for large refreshes |
| User-entered listings | Current listing comparison | User input | Listing | High | Avoid scraping Rightmove/Zoopla/SpareRoom without permission |

MVP geography decision:

- Rank MSOAs as the canonical recommendation areas.
- Use full postcode as a user/listing lookup key, not as the final recommendation grain.
- Roll LSOA, postcode, EPC, crime, planning, flood, and local-authority evidence up into MSOA-level area profiles with explicit confidence notes.

## Official Sources Checked

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

Models:

- `stg_landreg__transactions`
- `fct_sale_market`
- `rpt_area_market_context`

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
- For MVP, build affordability at local authority or BRMA level depending available table.
- Use property size where available.
- Add a caveat that official rent statistics are not live listing prices.

Models:

- `stg_ons__private_rents`
- `fct_rent_market`
- `rpt_area_affordability`

### ONS / Geography Postcode Lookup

URL: https://geoportal.statistics.gov.uk/

How to use:

- Prepare a local lookup snapshot with `scripts/prepare_onspd_seed.py` from an official CSV/ZIP; keep the full upstream file out of git.
- Use the normalized output to populate the postcode-to-LSOA/MSOA/local-authority/region bridge.
- Treat the committed `ref_onspd_sample` seed as a CI fixture, not as production geography coverage.
- Stamp the source snapshot date, source name, and source URL onto every row.

Models:

- `stg_geo__postcodes`
- `dim_postcode_geography`
- `dim_area`

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

Models:

- `stg_epc__certificates`
- `fct_epc_certificate`
- `rpt_area_energy_profile`

### Police API

URL: https://data.police.uk/docs/

Relevant facts checked:

- The API provides street-level crime and outcome data.
- It uses JSON web service endpoints over HTTP GET and POST.
- It includes crime-related and neighbourhood-related methods.

How to use:

- Aggregate monthly crime categories around area centroids or within area boundaries.
- Convert counts into rates using population denominators where available.
- Do not call areas "safe" or "unsafe"; show indicator levels and uncertainty.

Models:

- `stg_police__street_crime`
- `fct_crime`
- `rpt_area_safety_indicators`

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
- Add planning applications only with strong caveats about coverage.

Models:

- `stg_planning__entities`
- `fct_planning_constraint`
- `rpt_area_flood_planning_profile`

### Environment Agency Flood Monitoring

URL: https://environment.data.gov.uk/flood-monitoring/doc/reference

Relevant facts checked:

- Flood areas include Flood Alert Areas and Flood Warning Areas.
- The API provides geographic region information and polygons in GeoJSON/WGS84.
- Flood Alert Areas can cover broad areas where flooding is possible.

How to use:

- Treat this as flood-alert/flood-warning area context.
- For long-term risk, prefer official flood-risk-zone or risk-of-flooding datasets where licensing and bulk download are suitable.
- Show flood indicators as risk flags, not precise property-level predictions.

Models:

- `stg_flood__areas`
- `fct_flood_area_intersections`
- `rpt_area_flood_planning_profile`

### Transport / Commute

TfL URL: https://api-portal.tfl.gov.uk/

Relevant facts checked:

- TfL recommends registering for the Unified API.
- API requests use an `app_key` query parameter.
- TfL public open data can be used subject to transport data terms and conditions.

How to use:

- For MVP, start London-first if using TfL journey estimates.
- For UK-wide MVP, consider simpler public-transport access features first: nearest stations/stops, rail/tube/metro proximity, and estimated drive/cycle/walk times.
- For robust UK-wide routing, consider OpenTripPlanner with GTFS/NaPTAN/National Rail data, but that is a larger engineering task.

Models:

- `stg_transport__nodes`
- `fct_commute_sample`
- `rpt_area_commute`

### OpenStreetMap / Overpass

URL: https://wiki.openstreetmap.org/wiki/Overpass_API

Relevant facts checked:

- Overpass is a read-only API for querying OpenStreetMap data.
- Public instance usage policies matter, especially for larger refreshes.
- The wiki notes a general safe-use assumption on the main public instance for fewer than 10,000 queries per day and less than 1 GB downloaded per day, with identifying headers.

How to use:

- Use for amenities: supermarkets, parks, schools, gyms, libraries, rail stations, bus stops, pharmacies.
- For larger area refreshes, use extracts rather than hitting public APIs repeatedly.

Models:

- `stg_osm__amenities`
- `fct_amenity_access`
- `rpt_area_lifestyle`

## Data Model Notes

Core dimensions:

- `dim_date`
- `dim_area`
- `dim_postcode_geography`
- `dim_source`
- `dim_transport_node`

Core facts:

- `fct_sale_market`
- `fct_rent_market`
- `fct_epc_certificate`
- `fct_crime`
- `fct_planning_constraint`
- `fct_flood_area_intersection`
- `fct_commute_sample`
- `fct_amenity_access`
- `fct_user_listing`

Decision marts:

- `rpt_area_affordability`
- `rpt_area_commute`
- `rpt_area_safety_indicators`
- `rpt_area_energy_profile`
- `rpt_area_flood_planning_profile`
- `rpt_area_market_context`
- `rpt_neighbourhood_score`
- `rpt_tradeoff_explanations`

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
- Scores have source coverage/confidence fields.
- Missing data lowers confidence rather than silently becoming zero.

## MVP Source Order

1. Geography lookup.
2. ONS rent data.
3. Existing Land Registry sale-price data.
4. EPC data.
5. Police API.
6. Planning/flood constraints.
7. Transport/commute.
8. OSM amenities.
9. User-entered listing comparison.

This order gets to a useful renter/mover decision MVP without depending on live rental listing scraping.
