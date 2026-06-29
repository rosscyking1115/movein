# Deploy

Two services. Deploy the **API first** (the website build reads it to pre-render
the region hubs and sitemap), then the **website**.

```text
  API  →  Fly.io  (FastAPI container, decision.duckdb baked in, region lhr)
  Web  →  Vercel  (Next.js, root dir = web/)   [optionally behind Cloudflare]
```

---

## 1. API — Fly.io

Config: [`api/fly.toml`](api/fly.toml) + [`api/Dockerfile`](api/Dockerfile). App
name `uk-housing-decision-support-api`, region `lhr` (London), scales to zero.

Run these **from the repo root** — the Dockerfile copies `api/` + `data/decision.duckdb`,
so the build context must be the root (a root `.dockerignore` keeps the upload
small by dropping the 1.2 GB warehouse, `.venv`, and `web/`). Do **not** run
`fly launch` from the root — it ignores `api/fly.toml` and scaffolds a generic
Python app with the wrong name.

```bash
# one-time: claim the global app name from api/fly.toml
fly apps create uk-housing-decision-support-api

# deploy (reads api/fly.toml; build.dockerfile = api/Dockerfile, context = root)
fly deploy --config api/fly.toml

# lock CORS to the website origin once the web domain is known
fly secrets set CORS_ALLOW_ORIGINS="https://YOUR-DOMAIN,https://www.YOUR-DOMAIN" --config api/fly.toml
```

- Public URL: `https://uk-housing-decision-support-api.fly.dev` (use this as the
  website's `API_BASE_URL`).
- Health: `GET /healthz`. Docs: `/docs`.
- **CORS note:** the website talks to the API through its own same-origin BFF
  routes (`/api/*`), so tightening `CORS_ALLOW_ORIGINS` does **not** break the
  site — it only restricts direct browser calls. Default is `*` for dev.
- Data refresh = rebuild the image with a new `data/decision.duckdb` + `fly deploy`.

## 2. Website — Vercel

The Next.js app lives in `web/`, so the **Root Directory must be set to `web`**
in the Vercel project (Settings → General → Root Directory). Framework
(Next.js), build (`next build`) and output are auto-detected.

**Environment variables** (Settings → Environment Variables, Production):

| Var | Value | Notes |
|---|---|---|
| `API_BASE_URL` | `https://uk-housing-decision-support-api.fly.dev` | Server-only; the deployed Fly URL. |
| `NEXT_PUBLIC_SITE_URL` | `https://YOUR-DOMAIN` | Canonical origin, no trailing slash. Drives metadata, canonicals, sitemap, JSON-LD. |

Steps:

1. Import the GitHub repo into Vercel, set Root Directory = `web`.
2. Add the two env vars above (make sure the API is deployed first so the build
   can reach it — otherwise region hubs/sitemap defer to on-demand ISR).
3. Deploy. Add the custom domain in Settings → Domains.
4. (UK latency, Pro plan) set the function region to `lhr1`.

## 3. Optional — Cloudflare in front

Point the domain's DNS at Vercel through Cloudflare (proxied) for CDN, WAF and
per-IP rate-limiting. Keep "respect existing cache headers" on so Next's ISR
`Cache-Control`/`revalidate` still governs freshness. Tighten the API's
`CORS_ALLOW_ORIGINS` to the final origin(s).

## Post-deploy checks

- `GET /healthz` on the API returns `{"status":"ok","areas":7264,...}`.
- `https://YOUR-DOMAIN/` loads; the postcode box resolves to an area page.
- `https://YOUR-DOMAIN/sitemap.xml` lists area + town + rent + region URLs
  (~7,100). `https://YOUR-DOMAIN/robots.txt` points at it.
- A sample area page (`/area/<code>`) 308-redirects to its human slug and renders
  the receipt; check `view-source` for `<title>`, canonical and JSON-LD.
- A sparse area page is `noindex` (quality gate); a complete one is `index`.

## Data refresh

A refresh has two halves: a **local data build** (manual — it needs the large /
licensed source files), then an **automated deploy** (`.github/workflows/refresh.yml`).

**1. Build the new extract locally** (from the repo root, with the real sources
prepared — see the per-source steps in
[`HOUSING_DECISION_SUPPORT_DATA_SOURCES.md`](HOUSING_DECISION_SUPPORT_DATA_SOURCES.md)):

```bash
dbt run --select rpt_area_profile_mvp rpt_neighbourhood_score \
  --vars '{geo_source: onspd, epc_source: bulk, crime_source: bulk, \
           constraints_source: computed, amenities_source: computed}'
python scripts/build_decision_db.py        # → data/decision.duckdb
```

**2. Commit `data/decision.duckdb` to `main`.** That push triggers
`refresh.yml`, which **redeploys the API to Fly** (baking in the new extract) and
then **triggers a Vercel rebuild** so the website's ISR pages + sitemap regenerate
against the fresh data. You can also run it manually (Actions → *Data-refresh
deploy* → Run workflow).

**Required repository secrets** (Settings → Secrets and variables → Actions):

| Secret | How to get it |
|---|---|
| `FLY_API_TOKEN` | `fly tokens create deploy` (scoped to the app). |
| `VERCEL_DEPLOY_HOOK_URL` | Vercel → Settings → Git → Deploy Hooks (optional — without it, ISR picks up the new data within a day). |

The API exposes the extract's date as `data_vintage` in `/healthz` and `/v1/meta`,
so you can confirm a refresh shipped.

## Architecture notes

- `web` is a pure HTTP client of the API. Client components call same-origin
  `/api/*` BFF routes (`web/src/app/api/*`), which proxy to `API_BASE_URL`.
- Hubs/sitemap read the whole dataset via `GET /v1/areas/index` (one cacheable
  request). Area pages fetch a single area and are ISR-cached for a day.
- Security headers are set in [`web/next.config.ts`](web/next.config.ts) so they
  apply on any host.
