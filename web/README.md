# Website (Phase 2)

Next.js (App Router) frontend for the UK Housing Decision Support tool. It is a
pure HTTP client of the Phase 1 API (`../api`) — no direct DuckDB access. The API
is the keystone; this app and the mobile app are two clients of the same contract.

## Run locally

The site needs the API running. From the repo root:

```bash
# 1. API on :8000
.venv/Scripts/python -m uvicorn api.main:app --reload

# 2. Website on :3000 (in web/)
cd web
cp .env.example .env.local   # already points at http://127.0.0.1:8000
npm install
npm run dev
```

## Environment

| Var | Used by | Purpose |
|---|---|---|
| `API_BASE_URL` | server only | Base URL of the FastAPI service. |
| `NEXT_PUBLIC_SITE_URL` | metadata/sitemap/JSON-LD | Canonical site origin (no trailing slash). |

## Architecture

- **`src/lib/api.ts`** — server-side typed client for the API. `React.cache`
  dedupes per-area fetches across a page and its `generateMetadata`. Client
  components never import this; they call the same-origin BFF routes.
- **`src/app/api/*`** — thin BFF proxy routes (`/search`, `/listing-check`,
  `/resolve`) so client components stay same-origin and the API URL stays hidden.
- **`src/lib/reweight.ts`** — client mirror of `api/scoring.py` so the search
  sliders re-rank the visible pool instantly, with no round-trip.
- **`src/components/AreaReceipt.tsx`** — the hero "trade-off receipt": every score
  shown beside the raw fact behind it.

## Routes

| Route | Rendering | Notes |
|---|---|---|
| `/` | static (ISR 1d) | Postcode jump + value prop. |
| `/search` | dynamic | Server pool + on-device slider re-rank. |
| `/check` | static | Manual-entry listing checker. |
| `/area/[slug]` | dynamic (ISR 1d) | Programmatic SEO template. `/area/<code>` 308s to the human slug. |
| `/methodology` | static (ISR 1d) | Scoring + data sources (E-E-A-T). |
| `/sitemap.xml` | dynamic | Core pages + top tranche of quality-gated areas (staged indexation). |
| `/robots.txt`, `/llms.txt` | static | Crawler + AI-search hints. |

## SEO discipline

- **Quality gate** (`src/lib/quality.ts`): an area page is only `index`-ed and
  added to the sitemap if it clears a data-completeness bar (≥4/5 scores +
  amenities). Sparse areas render but stay `noindex` so they can't drag the
  site-wide quality signal.
- Each area page leads with a citable answer sentence + score, JSON-LD
  (`Place` / `BreadcrumbList`), and a canonical human slug.

## Not yet built (Phase 2 backlog)

- `/compare` multi-area view; `/town`, `/rent/[town]`, `/rankings/[region]` hubs
  and the dense internal-link mesh; expand sitemap tranche past the top 1,000.
- A slim `/v1/areas/index` API endpoint (id, name, region, completeness) would
  let `generateStaticParams` and the sitemap avoid paginating full `/v1/search`.
