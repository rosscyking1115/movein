# API — UK Housing Decision Support

A small **FastAPI** service over the decision marts. It ships the slim read-only
`data/decision.duckdb` extract, loads the 7,264 MSOA rows once, and serves the
explainable scores + a postcode resolver + a listing price check. The same
backend powers the website; a mobile client remains parked.

Interactive docs (Swagger) at `/docs`; OpenAPI schema at `/openapi.json` — use it
to generate typed clients for the web/mobile front ends.

## Endpoints (`/v2`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness + row count + data vintage |
| GET | `/v2/meta` | Components, default weights, scoring contract, data vintage |
| GET | `/v2/areas/{msoa_code}` | One MSOA's scores, facts, provenance, and evidence quality |
| GET | `/v2/areas/resolve?postcode=` | Postcode → MSOA (via postcodes.io) + its profile |
| POST | `/v2/search` | Weights + budget/region filters → re-ranked, paginated areas |
| POST | `/v2/listing-check` | Postcode + asking rent/price + bedrooms → area + neutral comparison figure and band |

`/v2/listing-check` returns `comparison_gbp` and `pct_vs_comparison`. For rent,
the comparison is the named local authority's official rent figure; for sales,
it is the MSOA median sold-price context. Neither is a valuation or a
"neighbourhood typical" price.

The `/v1` paths remain hidden compatibility aliases. Maintenance mode has no
scheduled removal date; removal would require an explicit future major-version
release and migration note. New clients should use `/v2`.

The weighted ranking re-runs from the stored 0–100 component scores, so clients
can also re-rank locally for instant slider response.

## Run locally

```bash
pip install -r api/requirements.txt
uvicorn api.main:app --reload --port 8080      # run from the repo root
# open http://localhost:8080/docs
```

## Deploy (Fly.io)

```bash
fly launch --no-deploy      # claim an app name; edit fly.toml if needed
fly deploy                  # builds api/Dockerfile, ships the extract
```

Scales to zero when idle. To refresh the data: rebuild `data/decision.duckdb`
(`scripts/build_decision_db.py`) and redeploy. Tighten CORS in `api/main.py` to
the website/app origins before launch.

## Caveats

Area-level indicators only — not a property valuation, never a "safe/unsafe"
label. Postcode resolution uses the free postcodes.io API; results are never
stored.
