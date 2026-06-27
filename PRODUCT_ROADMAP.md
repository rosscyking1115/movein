# Product Roadmap — from MVP to product

Date prepared: 2026-06-27

How `uk-housing-decision-support` evolves from a working Streamlit MVP into a real
product: an **API**, a **website**, a **mobile app**, and the **listing checker**
(paste a property URL → "is this a good area, and is the price reasonable?").

## Where we are

The hard part is built and **frontend-agnostic**: a tested dbt + DuckDB engine
over 9 open-data sources produces, per MSOA (7,264 England & Wales neighbourhoods):

- `rpt_neighbourhood_score` — five 0–100 component scores (affordability, safety,
  energy, flood, convenience), a weighted `overall_score`, confidence, and a
  "why this area" line. **Re-weighting is a weighted mean of 5 numbers** — cheap
  enough to do client-side.
- `rpt_area_profile_mvp` — the raw facts (rent, median sale price, EPC, crime,
  planning, flood, nearest amenities, walkable count).
- `dim_postcode_geography` — every UK postcode → MSOA.

The Streamlit app is the MVP. Everything below is a **frontend (or thin service)
on top of the same engine** — nothing is thrown away.

## The shape of the product

```text
  dbt + DuckDB engine  ──►  decision.duckdb extract  ──►  API (FastAPI)
                                                            │
                                              ┌─────────────┴─────────────┐
                                          Website (Next.js)        Mobile app (Expo)
                                              └─────── Listing checker ────┘
```

The **API is the keystone**: the website and the mobile app are just two HTTP
clients of it, and the listing checker is one of its endpoints surfaced in both.

---

## Workstream 1 — API (the foundation) ✅ built (`api/`)

> **Built:** a FastAPI service in `api/` — `/healthz`, `/v1/meta`,
> `/v1/areas/{msoa}`, `/v1/areas/resolve?postcode=`, `POST /v1/search` (weighted
> re-rank + budget/region filters), `POST /v1/listing-check`. Ships the
> read-only `decision.duckdb` in-memory; OpenAPI docs at `/docs`; Dockerfile +
> `fly.toml` (scale-to-zero). 7 API tests in CI. Deploy is one `fly deploy`.

**Stack: FastAPI (Python), standalone service.** Reuses the existing Python +
DuckDB engine with zero re-implementation, free OpenAPI docs (a typed contract for
web + mobile), Pydantic validation. A Next.js route handler was considered but
rejected — it would force a JS re-implementation of postcode→MSOA + DuckDB access
and couple the API to the web deploy.

**Data access:** ship the small read-only `decision.duckdb` extract *with* the API
(open once at startup, cache the 7,264 rows in memory). No external DB needed; the
2.7M-postcode lookup is a flat table. Refresh = ship a new file + redeploy.

**Endpoints (`/v1`):**
- `GET /areas/resolve?postcode=` → area scores + profile facts.
- `GET /areas/{msoa_code}` → direct fetch.
- `POST /search` (+ GET variant for CDN-friendliness) → weights + budget/region/EPC/flood
  filters → re-ranked results, paginated. (Clients can also re-rank locally from the
  returned component scores — instant slider response, no round-trip.)
- `POST /listing-check` → postcode + asking rent/price + bedrooms + type → area
  scores + price-vs-local-typical band.
- `GET /healthz`, `GET /meta` (data vintage / refresh date / default weighting).

**Hosting: Fly.io** (long-lived container, DuckDB baked into the image, UK/EU
regions) — recommended over Render/Railway (equivalent) and over Vercel serverless
(cold starts fight the in-memory-dataset design). Add Cloudflare in front for
`ETag`/`Cache-Control` (keyed on data vintage), per-IP rate limiting, tight CORS
allowlist, `/v1` versioning. Generate typed TS clients from the OpenAPI schema so
web + mobile stay in sync.

**Phases:** 0 skeleton + load extract → 1 resolve/by-code → 2 search → 3 listing-check
→ 4 hardening (cache, rate-limit, keys, deploy).
**Risks:** data-refresh cache coherence (mitigate with a vintage id in `ETag`/`/meta`);
DuckDB single-connection concurrency (threadpool / per-request cursor); postcode
normalisation + clean 404s for out-of-scope (Scotland/NI/retired).

---

## Workstream 2 — Website

**Stack: Next.js App Router on Vercel**, RSC-first, TypeScript, Tailwind. Rendering
chosen per route: SSG (home/methodology), **ISR for the ~7,264 area pages**
(pre-render flagship towns, lazily generate the long tail, revalidate on data
refresh), SSR for `/search` and `/check`.

**The growth engine — programmatic SEO over the area pages.** `/area/[msoa]` is one
template filled with genuinely different data per area, targeting real queries
("is *X* a good place to live", "*X* rent prices/crime/schools", "best areas to rent
in *town*"). Plus `/town/[town]`, `/rent/[town]`, `/rankings/[region]` hubs, `/compare`,
`/check`. Human slugs (`/area/e02000984-clapham-north-lambeth`).

**Make-or-break: thin-content discipline at 7k pages** (per `seo-audit` — the
helpful-content signal is *site-wide*, so weak pages drag down strong ones):
- Data-driven, non-substitutable content per page (real numbers, named amenities,
  a computed "why" line, comparison to town/region average).
- **Quality gate:** only index + sitemap an area page if data completeness clears a
  bar (e.g. ≥4/5 scores + ≥N amenities); `noindex` sparse areas until they fill in.
- Dense internal-link mesh (area ↔ nearby ↔ town ↔ region) so all 7k are crawlable;
  staged indexation (hubs + flagship towns first, then batches), sitemap index,
  302 postcode permutations → canonical area page.

**Structured data + AI-search:** JSON-LD `Place` / `FAQPage` / `BreadcrumbList` /
`Dataset`; lead each page with the answer sentence + score (citable by AI Overviews);
`llms.txt`; transparent methodology/data-sources pages for E-E-A-T.

**Performance (per `vercel-react-best-practices`):** parallelise the ~7 per-area API
fetches (`Promise.all` + `React.cache`), keep the map/charts `next/dynamic` + client-only
below the fold so area pages ship near-zero JS, stream slow blocks via `<Suspense>`.

**Design:** calm "map-and-ledger"; the **trade-off receipt** (score → raw fact →
comparison) is the hero. Thin BFF route handlers proxy the API (hide keys, tag-based
revalidation). Optional accounts/saved searches later, kept off the indexed path.

> **Skill note:** `programmatic-seo`, `schema`, `ai-seo` are *not installed* in this
> environment (only referenced inside `seo-audit`). Install them before the SEO build
> to wire in their exact checklists.

---

## Workstream 3 — Mobile app

**Stack: Expo (SDK 56) + Expo Router** — the user's existing stack (Journi). Native
tabs (Search · Compare · Check · Settings), a shared group route so **Area Detail**
pushes from any tab, React Query for server state, local state for the priority
weights.

**Screens:** onboarding (income / budget / weight sliders) → search (postcode→MSOA)
→ ranked list with **on-device live re-ranking** (component scores fetched once;
sliders re-sort instantly, animated, offline-capable) → **Area Detail = the trade-off
receipt** (component-score bars + raw facts + "why") → compare → listing checker.

**The native differentiator — share-in from Rightmove.** Universal/App Links ship
first (low risk): a verified domain + `check?url=` route. Then an **iOS Share
Extension** via `@bacons/apple-targets` (a config plugin — no ejecting) so the user
taps Share → our app from the Rightmove app; Android uses an `ACTION_SEND` intent
filter. Requires the backend listing→MSOA endpoint first.

**Data:** `expo/fetch` + React Query, long `staleTime` (static-ish dataset), AsyncStorage
persister + NetInfo for offline browse. **Deploy:** EAS Build/Submit to App Store +
Play; needs Apple ($99/yr) + Google ($25) accounts, store assets, privacy/data-safety
forms; EAS Update for OTA copy tweaks.

**Review/trust:** location permission with a clear purpose string; **indicator-not-verdict**
framing (never "safe/unsafe", always raw fact beside the score, visible sources) to
survive review and avoid defamation exposure; always show a human area name, never the
MSOA code.

---

## Workstream 4 — Listing checker (URL fetch + manual fallback)

**The candid legal finding drives the design.** Every major UK portal's Terms of Use
prohibit automated access/scraping; **Zoopla's robots.txt disallows `/property/`**
(the listing path); Rightmove's ToS bars spiders/crawlers/automated programs. A single
on-demand fetch of one user-pasted URL is *materially* different from bulk scraping
(no crawling/enumeration/harvesting) and the realistic exposure is contractual + IP,
not criminal — **but it is still a ToS breach, not "allowed."**

**The decisive risk is storage, not fetching** — UK **database right** protects the
portals' compiled data. So:

- **Manual entry is the product / default path.** User enters postcode + beds + type +
  asking figure; we resolve MSOA and analyse against **our own open/licensed data**
  (Land Registry, ONS) — zero portal dependency, zero ToS surface.
- **URL auto-fill is a best-effort accelerator only:** on-demand fetch *only* for
  domains whose robots.txt permits the listing path, parse JSON-LD/OpenGraph to
  **pre-fill a form the user confirms**, then **discard the fetched content** (persist
  only the user's confirmed inputs + our verdict). Transparent UA, hard rate limit,
  stop on 403/429, silent degrade to manual. **Never** reach into `window.PAGE_MODEL` /
  `__NEXT_DATA__`, spoof browsers, fetch Zoopla `/property/`, or cache portal content.
  Get legal sign-off before enabling this.

**Price-reasonableness:** compare the asking figure to our local typical and band it
(*well below / below / about typical / above / well above*), always paired with the
area receipt so "cheap" never reads as "good". **Highest-value data add: ingest ONS
PIPR rent BY BEDROOM (1/2/3/4-bed)** — currently we only hold the overall average, so a
1-bed looks cheap and a 4-bed expensive against it. PIPR publishes per-bedroom at LA
level (OGL — clean to store), mapped to MSOA. Sale listings compare to MSOA median sale
price with an explicit "asking ≠ sold" caveat. Always framed as an **area-level sanity
check, not a valuation**.

---

## Unified build sequence

Ordered by value-per-effort and dependency. Each phase ships something usable.

| Phase | What | Depends on | Why first/next |
|---|---|---|---|
| **0 — Quick wins (no new infra)** ✅ **done** | (a) **Listing checker, manual entry** (`app/pages/3_Listing_checker.py`) — postcode → MSOA via postcodes.io, area scores + price-vs-local; (b) **ONS PIPR per-bedroom rent** ingested (`rent_1bed_gbp`…`rent_4plus_gbp`) so the price check matches the listing's bed count | nothing | Shipped the most-requested feature with zero legal surface; per-bed rent is the biggest accuracy win. |
| **1 — API** ✅ **built** | FastAPI (`api/`): resolve / search / listing-check / meta, OpenAPI, Dockerfile + fly.toml. Deploy = `fly deploy` | Phase 0 data | The keystone every other client needs. |
| **2 — Website** | Next.js/Vercel: search + compare + **the 7,264 programmatic area pages** (SEO growth engine) + listing checker | API | Where organic growth comes from; the area pages are the moat. |
| **3 — Mobile** | Expo app: MVP screens + on-device re-rank; then **Rightmove share-in** (deep links → iOS share extension) | API | The native share-in is the standout differentiator. |
| **Cross-cutting** | Retire the legacy Streamlit dashboard once the website is live; data-refresh automation; analytics | — | — |

The current Streamlit app stays the **working demo** through Phases 0–2 and is retired
when the website covers its job.

## Decisions you'll need to make

- **API host** (recommend Fly.io) and a **domain name** for the product (drives the
  Streamlit/Pages slugs, the website, and mobile universal-link verification).
- **Apple Developer ($99/yr) + Google Play ($25)** accounts for the mobile app (Phase 3).
- **Legal sign-off** before enabling any URL auto-fill (Phase 3+); manual entry needs none.
- Whether to **install `programmatic-seo` / `schema` / `ai-seo`** skills before the website SEO build.
- Scope of **accounts/auth** (anonymous local-first is enough for a long time).

## Guiding principles (carried from the build plan)

- Official/open data first; **never scrape or store** portal content.
- Indicators with sources, **never "safe/unsafe" verdicts**; show uncertainty.
- Missing data lowers confidence, never silently scores zero.
- Area-level guidance, not property valuations.
