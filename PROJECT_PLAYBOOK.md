# Project Playbook — Lessons from Building MoveIn

A candid record of what worked, what failed, and the concepts worth stealing,
from building **MoveIn**: an explainable neighbourhood-comparison product for
England & Wales (7,264 areas, five open-data indicators, weighted search, map
UI). Written for teams building a similar artifact — a data product that ranks
real-world places/things and has to earn the user's trust while doing it.

---

## 1. The shape of the system (what we'd keep)

```
raw open data ──► dbt warehouse (DuckDB) ──► small "decision extract" (.duckdb, ~2.5 MB)
                                                      │
                                          FastAPI (Fly.io) — loads extract
                                          into memory once, serves /v1/*
                                                      │
                                          Next.js (Vercel) — server components
                                          fetch; client hits same-origin BFF
                                          routes that proxy the API
                                                      │
                                                   Browser
```

**Decisions that paid off:**

- **Ship a tiny read-only extract, not the warehouse.** The full warehouse is
  >1 GB; the decision extract is ~2.5 MB and contains exactly the columns the
  product needs. The API loads it into memory once (`lru_cache`) — no database
  server, no connection pooling, trivially cheap hosting. Data refresh = new
  file + redeploy. For data that changes monthly, this beats a live DB on
  every axis: cost, latency, reliability, and reasoning simplicity.

- **BFF proxy routes** (`/api/*` in Next.js relaying to the API). Client
  components never talk to the API origin directly. This hides the backend
  origin, sidesteps CORS entirely, and gives one place to shape errors
  (forward upstream status + detail instead of a blanket 500).

- **A typed contract file mirroring the API models** (`types.ts` ↔
  `models.py`), with a comment saying which is the source of truth. Not as
  good as generated types from OpenAPI (do that if you can), but the
  discipline of "one file, kept in sync, says so at the top" caught several
  drift bugs.

- **One `/v1/areas/index` endpoint returning the whole dataset** for hubs,
  sitemaps, and link meshes — cached daily. We started with dozens of search
  POSTs per page build; one cacheable GET replaced them all. If your dataset
  fits in a single response (<10 MB), add the index endpoint early.
  (Note: Next.js won't data-cache responses >2 MB per item — it logs a
  warning and refetches. Acceptable for build-time use; know it exists.)

- **Client-side re-ranking mirror.** Search sliders re-rank instantly because
  the scoring function (weighted geometric mean) is implemented twice: once in
  the API (pandas) and once in the client (~30 lines of TS). The pool comes
  from the server; the *ordering* is recomputed locally. Users get a live,
  zero-latency feel; the server only gets hit when filters actually change
  the pool. Duplicating 30 lines of math is far cheaper than a round-trip per
  slider tick. Put "mirrors api/scoring.py" comments on both sides.

- **Graceful degradation as a rule.** Every external dependency has a
  designed failure state: API down → page renders with a notice instead of
  crashing; no Maps API key → the map area shows setup instructions and the
  list still works. This turned several would-be outages into non-events.

## 2. Scoring & data concepts (the product's soul)

- **Indicators, never verdicts.** The product never says "safe/unsafe" or
  "good/bad" — it says "recorded crime is higher than in most areas — shown
  as a rate, not a label." This is both an ethics position and a legal
  posture, and it shaped everything: copy, colours, even the tooltip text.
  Decide this early; it's very hard to retrofit.

- **Scores are 0–100 percentile ranks** against the whole country. Percentiles
  are explainable ("higher than most areas") in a way z-scores never are.

- **Missing data is never zero.** If an indicator is absent, it's dropped from
  the weighted mean and the area's confidence level drops. Scoring a gap as 0
  silently punishes places for data coverage, not reality.

- **Weighted GEOMETRIC mean, not arithmetic.** One excellent pillar can't
  mask a terrible one. This is the right choice for "where should I live"
  (a place with 100 affordability and 10 safety is not a 55) — **but see
  §5: it confuses users, and you must explain it in the UI.**

- **Anchor the scale to the median** (median-anchored min-max before the
  geometric mean) so "50" means "typical area", which is how people read it.

## 3. UI design concept (transferable, not the pixels)

The identity concept: **a surveyor's schedule / receipt**. Every score sits
beside the raw figure it came from. The aesthetic follows the ethics.

- **Score-beside-fact, always.** Never show "71/100" without "58 crimes per
  1,000 residents" next to it. The number the user can verify builds trust in
  the number they can't. This is the single most transferable idea here.

- **Neutral score colours.** Score bars are one ink colour on a neutral
  track — never a red→green gradient, because red/green *is* a verdict. The
  only good/bad colours allowed are official external ones (EPC A–G bands),
  because those are the source's labels, not ours.

- **Mono/tabular numerals for all figures** (scores, rents, distances,
  ranks) so data reads like a ledger and columns of numbers align. Small
  thing; disproportionate effect on perceived rigour.

- **Footnote every indicator to its source** (ONS, Police.uk, EPC Register,
  Environment Agency, OSM) in a numbered source list, like a document, not a
  webapp. "Official open data" is the product's authority; show the receipts.

- **Explainability is a UI feature, not a docs page.** Weight sliders have
  named tags (Ignore / Minor / Some / Matters / High / Top), each indicator
  has an ⓘ popover (what it measures + source), and the weighting header has
  a legend explaining what the tags do — including one sentence on the
  geometric mean ("one weak pillar pulls an area down more than a strong one
  lifts it"). Users don't read methodology pages; they read the tooltip next
  to the thing they're touching.

- **Design the empty/failure states with the same voice** — "We don't yet
  hold this indicator for this area" beats a dash; "The data service is
  starting up" beats a spinner.

## 4. Map UX concepts

We migrated Leaflet/OSM → Google Maps mid-project. Concepts that survived:

- **The map is a backdrop; your data is the star.** Hide POI pins and most
  road labels (via cloud style or `clickableIcons={false}`), so your markers
  are the only thing competing for attention. Google Hotels / Airbnb / Zillow
  all do this; there's a reason.

- **Pills, not dots.** Markers that *show the number* (score or price) let
  users scan the map without hovering. A pill with a small tail reads as
  "label attached to a place".

- **Clusters must be branded and must show counts.** Default clusterer
  gradients look like a different product; a solid brand-colour circle with
  the count reads as "5 areas here — zoom in".

- **Hover-to-zoom** (`gestureHandling="greedy"`): scroll zooms the map when
  the cursor is over it, page scrolls otherwise. The "Ctrl+scroll to zoom"
  default feels broken to users comparing against Google's own products.

- **Click = preview, not navigate.** Clicking a result or pin focuses the
  map and opens a small overview (name, headline number, one CTA:
  "Show details →") with an explicit × close. Navigating away on first click
  loses the user's map context; they're mid-comparison, not done.

- **Muted vs colourful base map is a taste call — prototype both.** We built
  a fully desaturated style and a "colourful but decluttered" style (default
  palette, POI/transit/road-labels hidden) and let the owner A/B them in the
  style editor preview. Colourful-decluttered won.

- **Show all results.** We shipped a "top 40" cap with a list that said "200
  match" — users read the invisible 160 as *missing data* ("where's central
  London?"). If it matches, it must be reachable: cluster the map, scroll the
  list.

## 5. Mistakes we actually made (so you don't)

### The clustering saga (three attempts — the expensive lesson)
Rendering React-managed map markers into an imperative clusterer
(`@googlemaps/markerclusterer` + `@vis.gl/react-google-maps`) has exactly one
correct wiring, and we found it on the third try:

1. **Attempt 1:** markers in React state, inline `ref={(m) => ...}` callbacks
   in the parent's `.map()`. Inline refs get a **new identity every render**,
   so React 19 detaches/re-attaches every marker on every pass → each attach
   updated state → **infinite render loop**.
2. **Attempt 2:** markers in a mutable ref + `requestAnimationFrame`-coalesced
   sync. No loop — but markers attach *asynchronously* (after the Maps
   marker library loads), the sync logic raced it, and clustering silently
   never engaged in production. Silent, because nothing throws — you just
   see unclustered markers.
3. **Attempt 3 (correct, = the upstream example):** each marker is **its own
   component** whose ref callback is `useCallback`-stable; markers tracked in
   state; a `[clusterer, markers]` effect re-syncs. Stable refs mean no
   churn (no loop); state means every async attach re-runs the sync (no
   race).

**Meta-lessons:**
- When a library ships an official example for your exact use case, **start
  by copying it exactly.** Both failures were "clever" deviations. We only
  found the fix by diffing our code against
  `visgl/react-google-maps/examples/marker-clustering`.
- **React 19 treats changed ref-callback identity as detach+reattach.**
  Any inline ref inside a list render is a footgun if anything observes
  attach/detach. Per-item child components with stable callbacks is the
  pattern.
- When debugging integration code, **read the installed library source in
  `node_modules`** (10 minutes) before theorising (we burned longer than
  that on speculation). The clusterer's `render()` silently no-ops before
  the map projection exists, and its `clearMarkers()` doesn't hide anything —
  facts that instantly narrowed the search.

### Verification blind spots
- **Headless/background tabs cannot verify vector maps.** Google Maps
  deliberately waits for tab visibility; WebGL vector rendering and rAF are
  paused in hidden tabs. Our automated preview kept showing a static
  placeholder while everything "passed". A feature like this needs a
  **visible browser and human eyes** before merge — we merged a broken
  clustering fix (#30) that all automated checks approved.
- Corollary: rAF-based logic (attempt 2) **also doesn't run in hidden tabs**,
  so the harness couldn't even reproduce the failure.
- What automated checks *are* worth gating on: `tsc --noEmit`, ESLint, and a
  full production build (`next build`) — the build caught a shadowed global
  (`Map` component import vs `new Map()`) that dev mode tolerated.

### Perceived-data-gap bugs (the sneakiest class)
- The **top-40 cap** read as "your data is missing central London".
- The **geometric mean + a maxed 'Lower crime' slider** buried all of central
  London below rank 150 — again read as missing data. The *math was right*;
  the product failed to explain itself. Fixes were UI, not data: show all
  results, explain the weighting scale, one sentence on the mean's behaviour.
- On first load with no region filter, a *national* top-200 contained zero
  London areas (expensive city, affordability-weighted default) — "why is
  London empty?" Same lesson: **when honest ranking produces a surprising
  map, the surprise is a UX requirement.** Anticipate the "where is X?"
  question for whatever your users' anchor-favourite is.

### Google Maps Platform operational gotchas
- The JS API key is **public by design**; security = HTTP-referrer
  restrictions + restricting the key to only the Maps JavaScript API. Don't
  waste effort hiding it.
- **Referrer wildcards match whole subdomain labels only.**
  `https://*.myproject.vercel.app/*` does **not** match Vercel's
  per-deployment URLs (`myproject-a1b2c3-team.vercel.app` — the hash is glued
  into the same label). Add `https://*.vercel.app/*` or always browse via the
  stable production domain.
- Advanced Markers require a **Map ID**; `DEMO_MAP_ID` works but watermarks.
  Base-map styling for a Map ID lives in the **cloud console** (Map Styles →
  associate with Map ID), not in code — and the styling JSON has a **new
  format** (top-level `variant`/`styles`, dotted feature ids like
  `infrastructure.roadNetwork.road.local`); the old flat-array format is
  legacy-imported. Verify current schema in the docs rather than trusting
  a model's / your memory of the old format.
- `NEXT_PUBLIC_*` env vars are **baked at build time**. Set them in the
  hosting platform *before* the deploy that needs them, or expect a redeploy.
  Restriction/style changes on Google's side take ~2–5 min to propagate —
  wait before declaring failure.
- Expect ad-blockers to kill Google telemetry pings
  (`ERR_BLOCKED_BY_CLIENT`) — harmless noise; don't chase it.

### Smaller but real
- **Dynamic routes with server fetches feel frozen without `loading.tsx`.**
  One root `loading.tsx` (App Router convention) turned "is it broken?" into
  a branded quarter-second pulse. Ship it from day one.
- **Long-lived dev servers go stale after heavy HMR churn** — doubled
  mounts, dead handlers, phantom stale-chunk errors. Restart the dev server
  before concluding your code is broken; confirm fixes on a *fresh* compile.
- Background processes from earlier sessions squat on ports (`10048` bind
  errors on Windows). Check the port's PID instead of assuming your start
  command failed.
- If your framework version is newer than your tools'/assistant's knowledge,
  **keep the framework's bundled docs in `node_modules` and read them before
  writing code.** We kept a one-line repo instruction to that effect
  (`web/AGENTS.md`: "This is NOT the Next.js you know…") and it prevented
  several stale-API mistakes.

## 6. Process notes that made this smooth

- **Small PRs, merged in sequence** (#29 feature → #30 fix → #31 fix), each
  gated on typecheck + lint + prod build, each with an honest description
  including what was *not* verified ("visual cluster check needs a visible
  browser — verify after merge"). When #30 turned out wrong, the honest
  scope note made the follow-up unsurprising.
- **Human-verify visually before merge when the harness can't** — #31 was
  confirmed by the owner in a live preview *before* merging; #30 wasn't and
  shipped broken. The delta between those two outcomes is the process.
- **`.env.example` documents every variable with its failure mode** ("without
  it, the search page still works; the map shows a prompt"). Someone
  redeploying six months from now will thank you.
- **Deploy config is part of the change.** A frontend PR that needs a new
  env var isn't done until the hosting platform has it (and, for baked-in
  vars, the order is: set var → merge → deploy).

---

*Compiled 2026-07-02, after Phases 1–2 and the Google Maps search rework
(PRs #21–#23, #27–#31).*
