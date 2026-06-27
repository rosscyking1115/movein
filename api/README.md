# API — UK Housing Decision Support

A small **FastAPI** service over the decision marts. It ships the slim read-only
`data/decision.duckdb` extract, loads the 7,264 MSOA rows once, and serves the
explainable scores + a postcode resolver + a listing price check. The same
backend powers the renter app, the planned website, and the mobile app.

Interactive docs (Swagger) at `/docs`; OpenAPI schema at `/openapi.json` — use it
to generate typed clients for the web/mobile front ends.

## Endpoints (`/v1`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness + row count + data vintage |
| GET | `/v1/meta` | Components, default weights, data vintage |
| GET | `/v1/areas/{msoa_code}` | One MSOA's scores + facts |
| GET | `/v1/areas/resolve?postcode=` | Postcode → MSOA (via postcodes.io) + its profile |
| POST | `/v1/search` | Weights + budget/region filters → re-ranked, paginated areas |
| POST | `/v1/listing-check` | Postcode + asking rent/price + bedrooms → area + price-vs-local band |

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
