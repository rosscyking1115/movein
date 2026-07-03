# Mobile app — design handoff

The Expo app scaffold + data engine are built. **The full UI is to be designed
separately (Claude design).** This is the brief.

## What exists (don't rebuild)
- **Expo SDK 57** app (`mobile/`), Expo Router, `@expo/ui`, React Compiler +
  typed routes. Standard `create-expo-app` baseline + the additions below.
- **Data engine** in `src/lib/` — this is the contract every screen consumes:
  - `api.ts` — typed client for the FastAPI service (`getMeta`, `getArea`,
    `resolvePostcode`, `search`, `listingCheck`). Base URL from
    `EXPO_PUBLIC_API_URL`, defaults to the prod Fly service.
  - `types.ts` — the `Area` shape (5 component scores + raw facts) and requests.
  - `reweight.ts` — **on-device re-rank** (weighted geometric mean). This powers
    the headline feature: fetch scores once, sliders re-sort instantly, offline.
  - `query.tsx` — React Query provider (already wired into `app/_layout.tsx`),
    long `staleTime` because the dataset is static between releases.
- Default template screens (`src/app/index.tsx`, `explore.tsx`, `app-tabs.tsx`)
  are **placeholders** — replace them.

## Product principles (non-negotiable, carried from web + API)
- **Indicators, never verdicts.** Never "safe/unsafe" or "good/bad". Always show
  the raw fact beside the score (the "trade-off receipt").
- **Neutral score colours** — never red→green (that's a verdict). The only
  good/bad colours allowed are official EPC A–G bands.
- **Missing data lowers confidence**, never scores zero.
- Always show a human **area name**, never the raw MSOA code.
- Coverage is **England & Wales**; Scottish/NI postcodes get a friendly
  "on the roadmap" message (the API already returns it).

## Screens to design & build
1. **Onboarding** — budget + the five priority weight sliders (Affordability,
   Lower crime, Energy, Flood, Getting around). One-time setup.
2. **Search** (tab) — postcode/region entry → ranked list with **live on-device
   re-ranking** as sliders move (use `reweight()`), each row = score + raw facts.
3. **Area Detail** (pushes from any tab) — the trade-off receipt: component-score
   bars + the raw figure behind each + the "why this area" line.
4. **Compare** (tab) — up to 4 areas side by side.
5. **Check** (tab) — listing checker: postcode + beds + asking price → area
   scores + price-vs-local band (`listingCheck()`).
6. **Settings** (tab) — weights, data vintage, about/methodology, coverage note.

## Design system & skills to use
- **Native, platform-adaptive** styling per the `expo-building-native-ui` skill:
  inline styles + the `Color` API from `expo-router` (iOS UIKit + Android
  **Material 3** semantic colours), `NativeTabs`, Stack in `_layout.tsx`. **No
  NativeWind/Tailwind** — RN doesn't use it here.
- **`material-3`** skill → Android look (Compose/Material You tokens & components).
- **`swiftui-skills`** → iOS-native/HIG patterns — **requires macOS + Xcode**, so
  only usable when building/designing on a Mac.
- **`mobile-app-ui-design`** skill → cross-cutting mobile UX (hierarchy, thumb
  zone, spacing grid, empty states).
- **`@expo/ui`** (`expo-ui` skill) for genuinely native controls (grouped
  settings forms, sliders, sheets, menus) where plain RN falls short.

## Brand starting point (from the web "surveyor's ledger" identity)
Accent `#13476b`, ink `#172026`, muted `#6b7a82`, paper `#eff1ec`, neutral score
bar `#4a5c64`. Mono/tabular numerals for all figures. Map these onto the native
`Color` palette (`theme/colors.ts`) with light/dark variants — don't hardcode.

## Running / verifying
- `cd mobile && npm install && npx expo start`, then open in **Expo Go** (the
  skill: try Expo Go before custom builds). iOS simulator needs a Mac; on
  Windows use Expo Go on a device or the `eas-simulator` skill (cloud sim).
- Not yet runnable in CI here (no simulator on this box) — verify on device.

## The native share-in differentiator (later, needs a Mac/EAS)
Universal/App Links → `check?url=` first, then an iOS Share Extension via
`@bacons/apple-targets` so users share a Rightmove listing straight into the app.
Backend listing→MSOA endpoint already exists (`listingCheck`).
