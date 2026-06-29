# Handoff: MoveIn — neighbourhood safety & suitability indicator

## Overview
MoveIn is a web app that reads a UK neighbourhood from official open data and presents it as a surveyor-style "schedule" of indicators. Its core thesis: **every score sits next to the raw figure it came from**, and the product never delivers a verdict ("good", "safe") — only relative, evidence-backed indicators. It covers six routed views: Home, Area detail, Search (weighted ranking), Compare, Check-a-listing (price sanity check), Rankings, and Methodology.

## About the Design Files
The file in this bundle (`MoveIn.dc.html`) is a **design reference created in HTML** — a working prototype showing the intended look, content, and behavior. It is **not production code to ship as-is**. The task is to **recreate this design in the target codebase's existing environment** (React, Vue, SvelteKit, etc.) using that project's established component library, routing, and data-fetching patterns. If no codebase exists yet, pick the most appropriate framework (the prototype maps cleanly onto React with client routing) and build there.

The prototype is a single-component state machine with mock data baked in. In production, the area dataset and the typical-rent/price figures would come from real APIs (ONS, Land Registry, Police.uk, EPC Register, Environment Agency, OS/OSM).

## Fidelity
**High-fidelity (hifi).** Final colors, typography, spacing, and interaction behavior are all specified. Recreate the UI pixel-accurately using the codebase's libraries. Both a **light and dark theme** are fully defined (see Design Tokens) and must be supported.

## Brand
- **Name:** MoveIn
- **Logo (chosen mark — "gable house"):** an inline SVG drawn with theme color tokens, used in the header (26×26) and footer (22×22):
  ```html
  <svg width="26" height="26" viewBox="0 0 48 48" aria-hidden="true">
    <path d="M4 27 L24 11 L44 27" fill="none" stroke="var(--ink)" stroke-width="4.2" stroke-linejoin="miter"/>
    <line x1="9"  y1="27" x2="9"  y2="41" stroke="var(--ink)"   stroke-width="4.2"/>
    <line x1="39" y1="27" x2="39" y2="41" stroke="var(--ink)"   stroke-width="4.2"/>
    <line x1="7"  y1="41.5" x2="41" y2="41.5" stroke="var(--accent)" stroke-width="4"/>
  </svg>
  ```
  Roof + walls use `--ink`; the floor line uses `--accent`. The mark recolors automatically per theme.

## Layout shell (all routes)
- **Max content width:** 1140px, centered, 24px horizontal padding.
- **Header:** sticky, `top:0`, `z-index:20`, `background var(--paper)`, 1px bottom border `var(--rule)`, height 62px. Left→right: logo button (mark + "MoveIn" wordmark, gap 10px), nav buttons, and a theme toggle pushed right (`margin-left:auto`).
- **Nav buttons:** font 14px; active = weight 600, color `--ink`, background `--card2`; inactive = weight 500, color `--muted`, no background. 8px radius, min-height 38px, padding 8px 12px.
- **Theme toggle:** pill, `--card2` bg, 1px `--rule` border, color `--ink2`, radius 999px, padding 7px 13px, mono uppercase 11px, min-height 34px. Label is "Dark" in light mode / "Light" in dark mode.
- **Footer:** top border `--rule`, `--card2` bg. Logo + tagline (max 420px) on the left; two link columns ("Explore", "Sources") on the right (gap 48px). Bottom strip: 12px muted note, top border, 18px padding-top.
- **Route transition:** each `<section>` is keyed by `route:slug`; respects `prefers-reduced-motion` (animations collapse to ~0ms).

## Screens / Views

### 1. Home (`route: 'home'`)
- **Purpose:** State the thesis and let the user enter a postcode or jump to the worked example.
- **Hero:** max-width 780px, padding `74px 0 26px`. Mono eyebrow (12px, letter-spacing .18em, uppercase, `--accent`): "Official open data · England & Wales". H1 `clamp(40px,6.6vw,74px)`, line-height 1.02, display font. Lede paragraph 19px/1.6 `--ink2`, max 600px.
- **Postcode input:** rounded 10px card (`--card` bg, 1px `--rule2`), inline "Postcode" mono label + text input (mono 16px) + "Look up" button (`--accent` bg, white, radius 7px, height 42px). Enter key submits. Below: "Or explore a worked example → Chorlton, Manchester" (accent underlined link).
- **Trade-off receipt preview:** responsive grid `repeat(auto-fit,minmax(280px,1fr))`, gap 18px. Left card: receipt with a dashed perforation strip on top (`repeating-linear-gradient(90deg,var(--rule2) 0 5px,transparent 5px 11px)`, opacity .6), mono uppercase header "The trade-off receipt", then 4 rows (name + fact, a 74px track bar, mono score "/100"), and an italic sources note. Right column: three "principle" cards (`--card2` bg) numbered 01–03.
- **Popular row:** "Popular right now:" + pill buttons for 5 areas + "How we score →" accent link.

### 2. Area detail (`route: 'area'`, `slug`)
- **Purpose:** Full indicator schedule for one area, with provenance and a "what this means for you" rail.
- **Breadcrumb:** mono 12px "England & Wales › {region} › {LA}".
- **Header block:** flex, space-between, bottom border `--rule2`. Left: H1 `clamp(38px,5.4vw,60px)` area name, "{LA} · {region}", a citable sentence (17px). Right: **Composite** big mono number (62px) + "/100", "Rank {n} of 7,264"; and a **Confidence** mini bar-chart of 3 bars (heights 24/18/12px, filled `--accent` up to the confidence level, else `--rule2`) with capitalized label.
- **Two-column body:** grid `minmax(0,1.55fr) minmax(0,1fr)`, gap 26px.
  - **Receipt (left):** rounded 16px card, perforation strip on top. Header row "Indicator schedule" / "score · 0–100 · neutral scale". Each indicator row: name (+ optional "Your priority" outlined accent tag), measure with a superscript footnote, plain-language sentence; on the right a 26px mono score + "/100", a neutral progress bar with a median tick at 50%, and a percentile tick. **No-data state:** show "—" and a dashed "No data · not scored as zero" chip — never zero. Below each row, a provenance strip (`--card2`) showing the fact label + value; EPC value renders as a colored band chip (official A–G colors, see tokens). Footer: numbered Sources list.
  - **Right rail (sticky, top 78px):** "What this means for you" card (`--accent-wash` bg, `--accent-line` border): summary sentence; priority chips (Budget / Lower crime / Energy bills / Flood resilience / Getting around) that reorder the receipt (chosen indicators float to top and get `--accent-wash` row bg + the "Your priority" tag); when any chosen, a panel lists each chosen indicator's score + sentence; a fixed disclaimer about indicators-not-verdicts. Then two action buttons (Compare / Rank by my priorities). Then a "Full schedule of facts" card: rent-by-bedroom and area facts as `<dl>` rows.
- **Mesh links:** three columns — nearby areas in the same LA, browse links, and a "Checking a listing?" link into Check.

### 3. Search (`route: 'search'`)
- **Purpose:** Re-rank areas live by user-weighted indicators.
- **Layout:** grid `minmax(0,300px) minmax(0,1fr)`, gap 26px. Left sticky control card: five 0–5 range sliders (`accent-color:var(--accent)`, height 24px) labelled Affordability / Lower crime / Energy efficiency / Flood resilience / Getting around, each with a mono tag (Ignore/Minor/Some/Matters/High/Top); a "Max 2-bed rent" budget slider (600–2200 step 50, label shows "+/mo" at max); region filter chips.
- **Results:** a **position:absolute, transform-translateY animated list** — each card is absolutely positioned and animated to its rank slot (`transform .55s cubic-bezier(.22,.61,.36,1)`), filtered-out cards fade to opacity 0 and `pointer-events:none`. Row height 150px desktop / 186px narrow. Card: match score (30px mono) + rank label, area name (display 23px), "{LA} · {region} · {rent} 2-bed", and a row of five mini indicator bars (bar turns `--accent` when that indicator's weight ≥ 4). Container height animates with the result count.
- **Match formula:** weighted mean of available indicator scores; indicators with weight 0 are excluded; if all weights 0, equal-weight fallback over available indicators. Missing indicator values are skipped, never zero-filled.

### 4. Compare (`route: 'compare'`)
- **Purpose:** Up to 4 areas side by side.
- Chip row toggles areas (cap 4). A horizontally-scrollable table (`min-width:560px`) with a sticky first column. Two banded sections: **Scores · neutral 0–100** (each cell: mono value + small bar; the row leader is bold `--ink`, others `--ink2`) and **Facts · the evidence** (mono values). Caption: "Bold marks the highest score in each row — a reference point, not a recommendation."

### 5. Check (`route: 'check'`)
- **Purpose:** Area-level price sanity check for a listing (explicitly *not* a valuation).
- **Layout:** grid `minmax(0,340px) minmax(0,1fr)`, gap 26px. Left: form card — area `<select>`, deal toggle (To rent / To buy), bedrooms toggle (1/2/3/4+), and a £-prefixed asking-price input (mono). Right: a **price band** card with a horizontal scale (gradient track, center "typical" tick, animated marker positioned by `ratio = asking / typical`, marker left = `clamp(4%, 50% + (ratio-1)*220%, 96%)`), plus a headline+note that changes by band:
  - `<0.85` Well below · `<0.95` Below · `≤1.08` Around · `≤1.2` Above · `>1.2` Well above (the last uses `--caution` accent + border).
  - Empty state prompts for an asking price. Below: a mini area receipt with a "Full receipt →" link.

### 6. Rankings (`route: 'rankings'`)
- **Purpose:** Areas by equal-weight composite score (framed as a starting point, not a "best places" league).
- Region filter chips, then rows: national rank (#n, mono), area name (display 22px) + "{LA} · {region}", five mini indicator bars (hidden on narrow), composite number (26px mono), and a "→" open button.

### 7. Methodology (`route: 'methodology'`)
- **Purpose:** Explain the five indicators and, prominently, **what the product refuses to do**.
- Max-width 780px. Mono eyebrow "Methodology", H1 `clamp(34px,5vw,56px)`, lede. Then a `160px 1fr` grid listing each indicator (name + source + body). A `--accent-wash` callout: "What we deliberately don't do" with ✕ bullets (no "safe/unsafe/good/bad" labels; no red-to-green coloring; no zero-filling missing data; no individual-property valuation). Then a data-sources grid.

## Interactions & Behavior
- **Routing:** client-side; `go(route, slug?)` sets state and `window.scrollTo(0,0)`. Each section keyed by `route:slug` to retrigger its mount transition.
- **Theme toggle:** flips `dark` boolean; root CSS variables swap; `transition: background .3s, color .3s` on the root.
- **Search re-rank animation:** cards translateY to rank position over .55s; filtered-out fade out. Honor `prefers-reduced-motion` (set transition to `none`).
- **Priority chips (Area):** toggle reorders the receipt (chosen first) and reveals the priority panel.
- **Check marker:** animates left over `.5s cubic-bezier(.22,.61,.36,1)` when inputs change.
- **Postcode:** Enter key or "Look up" both route to the worked example (`chorlton`) in the prototype; in production, resolve the postcode to an area.
- **Responsive:** `isNarrow = viewport < 880px`; hides mini bars in rankings, taller search rows, grids reflow via `auto-fit`/`minmax`. Min hit targets ≥ 34px (chips/toggles) and 38–46px (nav/actions).

## State Management
Single component state:
- `route` (`'home'|'area'|'search'|'compare'|'check'|'rankings'|'methodology'`)
- `slug` (current area)
- `dark` (boolean theme)
- `displayFont` (`'Playfair Display'|'Newsreader'|'Spectral'`)
- `postcode` (string)
- `priorities` (map of indicatorKey→bool, Area page)
- `weights` ({affordability, safety, energy, flood, convenience} each 0–5; defaults 3/3/3/2/3)
- `budget` (number, default 2200), `region` / `rankRegion` (string filters)
- `compare` (array of up to 4 slugs)
- `check` ({areaSlug, deal:'rent'|'buy', beds:'1'|'2'|'3'|'4', asking:string})
- `reduce` (prefers-reduced-motion), `vw` (viewport width, updated on resize)

**Data layer:** in production replace the baked `AREAS` array and `IND` (indicator definitions: key, name, short, measure, source, high/low sentence builders, factLabel) with API responses. Keep the derived helpers: `matchScore`, `summaryFor`, `citableFor`, `factValue`, `epcColor`, `epcText`, currency formatters.

## Design Tokens

### Color — Light theme
| Token | Hex | Use |
|---|---|---|
| `--ink` | `#172026` | primary text |
| `--ink2` | `#3C4A52` | secondary text |
| `--muted` | `#6B7A82` | tertiary / labels |
| `--paper` | `#EFF1EC` | page background |
| `--card` | `#FBFCFA` | card surface |
| `--card2` | `#F2F4EF` | inset surface |
| `--rule` | `#DEE2D9` | hairline border |
| `--rule2` | `#CDD3C7` | stronger border |
| `--accent` | `#13476B` | primary accent (deep blue) |
| `--accent-wash` | `#E9EFF2` | accent tint bg |
| `--accent-line` | `#C2D2DC` | accent border |
| `--bar` | `#4A5C64` | neutral score bar |
| `--bar-track` | `#E0E4DB` | bar track |
| `--caution` | `#9A5B1E` | "well above" warning |

### Color — Dark theme
| Token | Hex |
|---|---|
| `--ink` | `#E9EDE7` |
| `--ink2` | `#B6C0B8` |
| `--muted` | `#7F8C84` |
| `--paper` | `#0F1518` |
| `--card` | `#161D22` |
| `--card2` | `#1B242A` |
| `--rule` | `#283238` |
| `--rule2` | `#37434A` |
| `--accent` | `#7BB8DA` |
| `--accent-wash` | `#16242C` |
| `--accent-line` | `#2C414C` |
| `--bar` | `#9DAEB6` |
| `--bar-track` | `#283238` |
| `--caution` | `#D69A5A` |

### EPC band colors (fixed, both themes — official government bands)
`A #008054` · `B #19B459` · `C #8DCE46` · `D #FFD500` · `E #FCAA65` · `F #F18A31` · `G #E9153B`. Text color over band: dark `#1a1a1a` for C/D/G-light cases, white for A/B/E/F (see `epcText`). These are the **only** colors allowed to imply good/bad — score bars stay neutral (`--bar`).

### Typography
- **Display (headings, wordmark, area names):** Playfair Display (default), weight 700. Alternates supported: Newsreader (600), Spectral (600). Stack falls back to Georgia, Times New Roman, serif.
- **Body / UI:** IBM Plex Sans (400/500/600/700), `system-ui` fallback.
- **Mono (eyebrows, scores, numbers, tags):** IBM Plex Mono (400/500/600).
- Eyebrows: 11–12px, letter-spacing .12–.18em, uppercase, mono.
- H1: `clamp(34–40px … 56–74px)` per route (values above), line-height ~1.02–1.05.
- Scores: mono, 26px (rows) / 30px (search match) / 62px (composite).

### Spacing / radius / shadow
- Content max-width 1140px; section paddings 30–74px top.
- Card radius: 14–16px (major cards), 9–11px (chips/insets), 999px (pills), 7–10px (buttons).
- Card shadows: `0 1px 2px rgba(20,30,40,.04)` (subtle), `0 2px 5px rgba(20,30,40,.05)` (receipt).
- Gaps: grids 18–26px; chip rows 6–10px.
- Perforation strip: `repeating-linear-gradient(90deg,var(--rule2) 0 5–6px,transparent 5–6px 11–13px)`, opacity .55–.6.

### Motion
- Route/search: `transform .55s cubic-bezier(.22,.61,.36,1), opacity .35s ease`.
- Check marker: `left .5s cubic-bezier(.22,.61,.36,1)`.
- Theme: `background .3s, color .3s`.
- All collapse to ~0ms under `prefers-reduced-motion: reduce`.

## Assets
- **Logo:** inline SVG only (gable house, code above) — no raster assets.
- **Fonts:** Google Fonts — Playfair Display, Newsreader, Spectral, IBM Plex Sans, IBM Plex Mono. Self-host or load via the codebase's font pipeline.
- **No icons library** is used beyond the inline SVG mark, "→" / "›" / "✕" glyphs.

## Files
- `MoveIn.dc.html` — the complete hifi prototype (all 7 routes, both themes, full mock dataset and logic). This is the single source of truth for layout, copy, tokens, and behavior. Open it in a browser to interact with every state.

## Notes for implementation
- The "indicators, not verdicts" stance is a **product principle, not decoration** — preserve the neutral bar coloring, the "no data ≠ zero" treatment, the median tick, and the methodology refusals.
- All user-facing copy in the prototype is final; lift it verbatim unless the codebase has a content system.
- Numbers in the dataset are representative open-data figures for a worked example, not live data — wire to real sources in production.
