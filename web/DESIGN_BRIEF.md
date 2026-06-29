# Website Design Brief — UK Housing Decision Support

A brief for **Claude Design** to lead a **fresh visual identity** for the website
(`web/`). The site is already built and live; this is a design-led reskin, not a
rebuild. Read the "Do not break" section as hard as the creative one.

> **Decisions already made by the client:**
> 1. **Fresh, distinctive direction** — a new identity grounded in the subject,
>    not a polish of today's look. Take one real, justified aesthetic risk.
> 2. **Adopt shadcn/ui** as the component foundation (Next 16 + Tailwind v4),
>    themed to the new identity.

---

## 1. The subject, in one breath

A tool that helps people **decide where to live in England & Wales** using only
**official open data**, presented as **honest indicators — never verdicts**. For
every neighbourhood (7,264 of them) it shows five 0–100 scores *and the raw fact
behind each one*. The product's soul is **transparency: no number is asked to be
trusted on its own.**

- **Audience:** renters and buyers weighing a move — stressed, sceptical, doing a
  high-stakes life decision. Also Google/AI search traffic landing cold on a
  single area page. Range from data-savvy to data-wary; design for the wary.
- **The page's one job:** let someone judge a place honestly and quickly — score,
  then the evidence, then "compared to what?"
- **The goal behind the goal:** organic search. This is a 7,000-page programmatic
  SEO engine. The design has to read as **credible and well-sourced** (E-E-A-T)
  and stay **fast and light**, or it doesn't rank.

## 2. The signature: the "trade-off receipt"

This is the one element the site should be remembered by, and it already exists in
spirit — **elevate it into the centrepiece**. Every component score sits **beside
the raw fact it came from**: a score is a *line item*, the fact is its
*provenance*. Lean into the metaphor — itemised, auditable, evidence-led, like a
receipt or a surveyor's schedule where every figure is sourced. Spend your
boldness here; keep everything around it quiet.

The area page (`/area/[slug]`) is the hero surface and the most-visited page.
Design *it* first; the rest of the system follows from it.

## 3. Non-negotiables (these constrain the aesthetic — honour them)

These come from the product's ethics and its legal posture. Breaking them isn't a
style choice, it's a defect.

1. **Indicators, not verdicts. Never "safe/unsafe."** No word or visual implies a
   place is good or bad — only higher/lower on a measured indicator, with the fact
   shown.
2. **Therefore: scores must NOT use red→amber→green "good/bad" colour-coding.**
   This is the trap every dashboard falls into. Score bars/figures stay
   **neutral** — one accent, or a single-hue intensity ramp, never a diverging
   judgemental scale. (Exception: the **EPC A–G** rating may use its *official*
   government band colours — that's a recognised national standard, not our verdict.)
3. **Show the fact beside the score.** Provenance is the brand. Never a lone number.
4. **Show uncertainty honestly.** Missing data lowers *confidence*; it is never
   scored as zero. Design explicit "—" / "no data" / confidence states; don't hide
   gaps.
5. **Area-level, not a property valuation.** Copy and framing stay at neighbourhood
   level. The listing checker is an area-level *sanity check*; "asking ≠ achieved."
6. **Always a human area name, never the raw MSOA code.** (`area_name` is e.g.
   "Westminster 018" — show that, never "E02000977".)

## 4. Creative direction — go fresh, but earn it

**What to beat:** today's UI is functional but **templated** — warm off-white
"paper," hairline rules, a single green accent, default Geist fonts. That is
*literally one of the three clichéd AI-default looks*. The new identity must not be
another one of them. **Avoid all three defaults:** (a) cream/serif/terracotta
broadsheet; (b) near-black + one acid-green/vermilion accent; (c) hairline-rule
newspaper columns. Also avoid a **GOV.UK clone** (we want *trust*, not *bureaucracy*).

**Where to find a distinctive direction — mine the subject's own world.** A few
provocations (pick, blend, or beat them — don't do all):

- **The surveyor's dossier / official report** — precise, annotated, evidence-led,
  with visible provenance (every figure footnoted to its source). Plays straight to
  E-E-A-T and the "receipt" signature.
- **Cartographic / Ordnance Survey** — UK mapping vernacular: fine linework, contour
  or grid motifs, a restrained survey palette, grid-reference typographic details.
- **Civic data-journalism** — the seriousness of FT/Economist data design applied to
  a public-good tool: confident charts, impeccable typographic hierarchy, restraint.

Whatever the direction:

- **Typography is the personality.** Pick a deliberate pairing that is *not* the
  Geist/Inter default: a characterful **display** face used with restraint, a
  workhorse **body** face, and a true **mono/tabular** face for figures. **Numbers
  are the product** — tabular figures everywhere a score, rent, distance or rank
  appears; make the number treatment itself memorable.
- **Palette:** 4–6 named hex values. Must keep scores neutral (see non-negotiable
  #2). Choose something credible and ownable — not cream-and-terracotta.
- **Structure encodes meaning, not decoration.** If you use numbering/eyebrows/
  dividers, they must mean something (rank, sequence, provenance) — don't add
  01/02/03 unless the content is truly a sequence.
- **Motion: restrained.** One earned moment beats scattered effects. The obvious
  candidate already exists: the **search list re-ranking** as the priority sliders
  move — make that reorder feel alive. Respect `prefers-reduced-motion`.

## 5. Foundation & technical constraints

- **Stack:** Next.js **16** (App Router, RSC-first), **Tailwind v4** (`@theme`
  tokens in `globals.css`), TypeScript. Server Components by default; client
  components only where interaction needs them (sliders, compare controls, postcode
  box, listing form).
- **shadcn/ui (adopt):** initialise `components.json`; build on shadcn primitives
  and theme them to the new identity via semantic tokens (`bg-primary`,
  `text-muted-foreground`, …). Use the right primitives:
  - Forms → `Field` / `FieldGroup` (not raw divs); validation via `data-invalid` +
    `aria-invalid`.
  - Option sets (bedrooms, deal type, region chips, weight presets) → `ToggleGroup`.
  - Overlays → `Dialog`/`Sheet` with required `*Title`.
  - Style with variants/`size-*`; `className` for layout only; semantic tokens over
    raw colours.
- **Performance (this is SEO-critical):** ~6,500 area pages are ISR. Keep them
  **near-zero client JS** — the receipt is static server-rendered HTML. Any
  map/chart is `next/dynamic`, client-only, **below the fold**, lazy. Don't pull
  heavy libs into the shared bundle. Don't regress Lighthouse.
- **Data you can show (per area):** `area_name`, `local_authority_name`, `region`;
  scores `overall_score`, `overall_rank`, `confidence_level`, `why_this_area`, and
  `affordability/safety/energy/flood/convenience_score` (0–100); facts
  `official_rent_monthly_gbp`, `rent_1bed/2bed/3bed/4plus_gbp`,
  `median_sale_price_gbp`, `epc_median_rating` (A–G), `crime_rate_per_1000`,
  `flood_risk_flag`, `walkable_amenity_count`, `nearest_station/supermarket/gp/
  school/greenspace_km`. **No street-level or property data, and no map geometry
  today** (a map is an optional enhancement, not a given).

## 6. Page-by-page inventory

The information architecture and routes are fixed (SEO depends on them). Redesign
the surfaces, not the URLs.

| Route | Job | Key elements |
|---|---|---|
| `/` (home) | Sell the premise; route in | Hero (the thesis — lead with the receipt idea, not a generic big-number); postcode jump → area; 3 principles; methodology CTA |
| `/area/[slug]` **(hero)** | Judge one place honestly | **The trade-off receipt**: overall score + rank + confidence, the "why" line, 5 component rows (neutral bar + the fact), full facts grid (per-bed rents, sale price, EPC, crime, flood, amenities + distances), compare/rank CTAs, town/region/rent mesh links |
| `/search` | Rank by *my* priorities | 5 weight sliders (live, on-device re-rank), budget + region filters, ranked result cards |
| `/compare` | Weigh up to 4 places | Side-by-side table: scores section (bold the row leader) + facts section (neutral) |
| `/check` | Is this listing's area + price sane? | Form (postcode, rent/buy, beds, asking) → price-vs-local band + the area receipt |
| `/rankings`, `/rankings/[region]` | Browse the best areas | Region index; region leaderboard + local-authority chips |
| `/town/[town]` | Best areas in a town/LA | Ranked area cards + "rent in X" CTA |
| `/rent/[town]` | "Rent in X" by bedroom | LA per-bed averages + cheapest-first table |
| `/methodology` | Earn trust (E-E-A-T) | The 5 indicators, the scoring, "what we deliberately don't do," data sources |
| `/not-found`, nav, footer | — | Global frame; footer carries the trust line + source links |

## 7. Component system (the reusable kit)

Design these as a coherent set — most pages are made of them:

- **ScoreBar** — the most-repeated atom. Neutral, non-verdict. A score (0–100) with
  its bar; needs a distinctive-but-honest treatment and a clear "no data" state.
- **AreaReceipt** — the signature composite (header + why line + component ledger +
  facts grid). The thing to get right.
- **AreaCard** — result row for search/hubs: match/overall score, place, rent, and
  the five mini component bars (the ranking must be legible, not a black box).
- **CompareTable** — dense, scannable, responsive (horizontal scroll on mobile).
- **PriceBand** — listing-check verdict (well below → well above the local typical),
  worded as a prompt to look closer, not a "good/bad deal." Only "well above" gets
  emphasis, and even then as caution, not alarm.
- **Forms** — postcode box, the slider panel, the listing form (shadcn `Field`s).
- **Number/figure style** — tabular, mono, consistent units (`£1,450/mo`, `0.8 km`,
  `72/100`).
- **Confidence & empty states** — first-class, not afterthoughts.

## 8. Copy & voice

- Plain, active, end-user language. Name things by what people recognise.
- **Indicators, not verdicts**, in every label and microcopy. Never "safe"/"good
  area."
- Errors explain what to do, don't apologise, aren't vague. Empty states invite
  action ("Add an area to compare," not "No data").
- Consistent action vocabulary (a button that says "Compare" leads to a "Compare"
  view). Sentence case.

## 9. Accessibility & performance gates (must pass)

Run the output against the **`web-design-guidelines`** and
**`vercel-react-best-practices`** skills. Minimums:

- WCAG AA contrast (≥4.5:1 text); visible keyboard focus on every interactive
  element; correct semantics (real `<table>` for compare, `<dl>` for facts, labels
  on inputs).
- Hit targets ≥24px; sliders and toggles keyboard-operable and announced.
- `prefers-reduced-motion` respected; no layout shift; images sized.
- Area pages stay light (server HTML; deferred client JS); no Lighthouse regression.

## 10. Do **not** break (SEO + architecture are load-bearing)

- **Routes/IA, slugs, and canonicals** — incl. `/area/<code>` → human-slug 308.
- **`generateMetadata`, JSON-LD** (`Place`/`BreadcrumbList`/`ItemList`), the
  **citable answer sentence** that leads each area page (AI Overviews lift it), and
  the **noindex quality gate** for sparse areas.
- **ISR / revalidate** behaviour and the **server/BFF data flow** (`src/lib/api.ts`,
  `src/app/api/*`). This is a styling + structure pass — **don't change the data
  contract** (the `Area` shape) or how data is fetched.
- `sitemap.ts`, `robots.ts`, `llms.txt`.

## 11. Deliverables expected from Claude Design

1. A **design plan first** (per `frontend-design`): named palette (4–6 hex), the
   type pairing + scale, layout concept, and the **one signature element** — with a
   note on the aesthetic risk taken and why it's not a default.
2. **Theme tokens** (Tailwind v4 `@theme` + shadcn theme) and the restyled
   component kit (§7).
3. **All page surfaces** (§6), responsive to mobile, a11y-complete.
4. Screenshots of the area page, search, compare, and home for review before merge.

## 12. Open questions (flag, don't block)

- **Domain:** site is on `*.vercel.app` for now; final domain TBD (affects nothing
  visual).
- **Map:** worth adding a lightweight area map? High visual value, but must be
  lazy/below-the-fold to protect performance. Treat as optional v2.
- **Dark mode:** in scope? (Currently light-only.) Designer's call within the
  identity.
