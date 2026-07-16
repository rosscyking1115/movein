"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useMemo, useRef, useState } from "react";
import type { Area, ComponentKey, SearchResponse } from "@/lib/types";
import { reweight } from "@/lib/reweight";
import { areaSlug } from "@/lib/slug";
import { rentPerMonth, score as fmtScore } from "@/lib/format";
import { InfoPopover } from "./InfoPopover";

// MapLibre touches window, so load the map client-only.
const SearchMap = dynamic(() => import("./SearchMap"), {
  ssr: false,
  loading: () => <div className="h-[380px] w-full animate-pulse rounded-[14px] border border-rule2 bg-card2" />,
});

const SLIDERS: { key: ComponentKey; label: string; abbr: string }[] = [
  { key: "affordability_score", label: "Affordability", abbr: "Aff" },
  { key: "safety_score", label: "Lower crime", abbr: "Crm" },
  { key: "energy_score", label: "Energy efficiency", abbr: "Ene" },
  { key: "flood_score", label: "Flood resilience", abbr: "Flo" },
  { key: "convenience_score", label: "Getting around", abbr: "Get" },
];
const TAGS = ["Ignore", "Minor", "Some", "Matters", "High", "Top"];

// What each indicator measures + its source, shown in the per-slider info popover.
const INDICATOR_HELP: Record<ComponentKey, { measures: string; source: string }> = {
  affordability_score: {
    measures: "Official local-authority rent context and MSOA sale-price context versus the rest of England & Wales. Higher score = more affordable.",
    source: "ONS Price Index of Private Rents; HM Land Registry.",
  },
  safety_score: {
    measures: "Recorded crime, as a rate per 1,000 residents. Higher score = less recorded crime. It is a rate, never a safe/unsafe label.",
    source: "Police.uk street-level open data.",
  },
  energy_score: {
    measures: "Median home energy rating (EPC) — a proxy for heating bills. Higher score = more efficient homes.",
    source: "EPC Register.",
  },
  flood_score: {
    measures: "Environment Agency flood-risk band. Higher score = lower flood risk.",
    source: "Environment Agency / planning.data.gov.uk.",
  },
  convenience_score: {
    measures: "Shops, services and transport within walking reach. Higher score = more within reach.",
    source: "OpenStreetMap.",
  },
};

// The 0–5 weight scale, explained once in the header popover.
const SCALE_HELP: [string, string][] = [
  ["Ignore", "Left out of the ranking entirely (weight 0)."],
  ["Minor", "Counts a little."],
  ["Some", "Counts a bit more."],
  ["Matters", "A solid, balanced weight."],
  ["High", "Pulls the ranking strongly."],
  ["Top", "The single biggest driver of the ranking."],
];

const REGIONS = [
  "North East", "North West", "Yorkshire and The Humber", "East Midlands",
  "West Midlands", "East of England", "London", "South East", "South West", "Wales",
];

const DEFAULT_WEIGHTS: Record<ComponentKey, number> = {
  affordability_score: 3, safety_score: 3, energy_score: 3, flood_score: 2, convenience_score: 3,
};
const ROW_H = 162;
const BUDGET_MIN = 600;
const BUDGET_MAX = 5000; // at the max the filter is treated as "no limit"
const BUDGET_STEP = 100;

export function SearchClient({
  initialAreas,
  initialRegions,
}: {
  initialAreas: Area[];
  initialRegions: string[];
}) {
  const [weights, setWeights] = useState<Record<ComponentKey, number>>(DEFAULT_WEIGHTS);
  const [regions, setRegions] = useState<string[]>(initialRegions);
  const [budget, setBudget] = useState(BUDGET_MAX);
  const [pool, setPool] = useState<Area[]>(initialAreas);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Area | null>(null);
  const mapWrap = useRef<HTMLDivElement>(null);

  const effective = useMemo(() => {
    const sum = Object.values(weights).reduce((a, b) => a + b, 0);
    if (sum > 0) return weights;
    return Object.fromEntries(SLIDERS.map((s) => [s.key, 1])) as Record<ComponentKey, number>;
  }, [weights]);

  // Sliders re-rank the visible pool instantly — no network. Every matching area
  // is shown (the map clusters them); nothing is hidden behind a top-N cap.
  const ranked = useMemo(() => reweight(pool, effective), [pool, effective]);

  // Selecting an area focuses the map (pan/zoom + InfoWindow) and, on narrow
  // screens where the map sits above the list, scrolls it back into view.
  const select = (area: Area | null) => {
    setSelected(area);
    if (area) mapWrap.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  // Filters (region/budget) change the pool, so they need a fresh fetch. A plain
  // function (recreated each render) captures the latest weights for ordering.
  async function fetchPool(regs: string[], bud: number) {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          weights: effective,
          regions: regs.length ? regs : null,
          max_rent: bud < BUDGET_MAX ? bud : null,
          limit: 200,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Search failed.");
      setSelected(null);
      setPool(((await res.json()) as SearchResponse).results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }

  // Region toggles apply immediately; the budget slider is debounced.
  const toggleRegion = (r: string) => {
    const next = regions.includes(r) ? regions.filter((x) => x !== r) : [...regions, r];
    setRegions(next);
    fetchPool(next, budget);
  };

  const budgetTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const onBudget = (v: number) => {
    setBudget(v);
    clearTimeout(budgetTimer.current);
    budgetTimer.current = setTimeout(() => fetchPool(regions, v), 400);
  };

  const chip = (active: boolean) =>
    `cursor-pointer rounded-full border px-2.5 py-1 text-xs transition-colors ${
      active
        ? "border-accent bg-accent text-white"
        : "border-rule2 text-ink2 hover:border-accent-line hover:bg-accent-wash hover:text-ink"
    }`;

  return (
    <div className="grid items-start gap-[26px] lg:grid-cols-[minmax(0,300px)_minmax(0,1fr)]">
      {/* Controls */}
      <div className="rounded-[16px] border border-rule2 bg-card p-[22px] lg:sticky lg:top-[78px]">
        <div className="mb-[18px] flex items-center justify-between">
          <span className="font-mono text-[11px] uppercase tracking-[.12em] text-ink">Weight each indicator</span>
          <InfoPopover label="What the weights mean" align="right">
            <div className="mb-1.5 text-[13px] font-semibold text-ink">How weighting works</div>
            <p className="mb-2 text-[12px] leading-[1.5] text-ink2">
              Drag a slider right to make that indicator count for more. The tag shows its strength:
            </p>
            <ul className="mb-2 space-y-1">
              {SCALE_HELP.map(([tag, meaning]) => (
                <li key={tag} className="flex gap-2 text-[12px] leading-[1.4]">
                  <span className="w-[52px] flex-shrink-0 font-mono text-accent">{tag}</span>
                  <span className="text-ink2">{meaning}</span>
                </li>
              ))}
            </ul>
            <p className="text-[12px] leading-[1.5] text-muted">
              Match blends your five 0–100 scores with a geometric mean, so one weak pillar pulls an
              area down more than a strong one lifts it.
            </p>
          </InfoPopover>
        </div>
        {SLIDERS.map((s) => (
          <div key={s.key} className="mb-[18px]">
            <div className="mb-[7px] flex items-baseline justify-between">
              <span className="flex items-center gap-1.5">
                <label htmlFor={s.key} className="text-sm font-semibold text-ink">{s.label}</label>
                <InfoPopover label={`About ${s.label}`}>
                  <div className="mb-1.5 text-[13px] font-semibold text-ink">{s.label}</div>
                  <p className="mb-2 text-[12px] leading-[1.5] text-ink2">{INDICATOR_HELP[s.key].measures}</p>
                  <p className="text-[11px] leading-[1.4] text-muted">
                    Source: {INDICATOR_HELP[s.key].source}
                  </p>
                </InfoPopover>
              </span>
              <span className="font-mono text-xs text-accent">{TAGS[weights[s.key]]}</span>
            </div>
            <input
              id={s.key}
              type="range"
              min={0}
              max={5}
              step={1}
              value={weights[s.key]}
              onChange={(e) => setWeights((w) => ({ ...w, [s.key]: Number(e.target.value) }))}
              aria-label={`${s.label} importance`}
              className="h-6 w-full cursor-pointer accent-[var(--accent)]"
            />
          </div>
        ))}
        <div className="mt-1.5 border-t border-rule pt-4">
          <div className="mb-2.5 flex items-center justify-between text-xs uppercase tracking-[.06em] text-muted">
            <span>Filters</span>
            {loading && <span className="font-mono text-[10px] normal-case tracking-normal text-accent">updating…</span>}
          </div>
          <label htmlFor="budget" className="mb-1.5 block text-[13px] text-ink2">
            Max rent ·{" "}
            <span className="font-mono text-ink">{budget >= BUDGET_MAX ? "no limit" : `£${budget.toLocaleString("en-GB")}/mo`}</span>
          </label>
          <input
            id="budget"
            type="range"
            min={BUDGET_MIN}
            max={BUDGET_MAX}
            step={BUDGET_STEP}
            value={budget}
            onChange={(e) => onBudget(Number(e.target.value))}
            aria-label="Maximum monthly rent"
            className="mb-4 h-6 w-full cursor-pointer accent-[var(--accent)]"
          />
          <div className="mb-2 text-[13px] text-ink2">Region</div>
          <div className="flex flex-wrap gap-1.5">
            {REGIONS.map((r) => (
              <button key={r} type="button" onClick={() => toggleRegion(r)} aria-pressed={regions.includes(r)} className={chip(regions.includes(r))}>
                {r}
              </button>
            ))}
          </div>
          {regions.length > 0 && (
            <button
              type="button"
              onClick={() => { setRegions([]); fetchPool([], budget); }}
              className="mt-2.5 cursor-pointer text-xs text-accent hover:underline"
            >
              Clear regions
            </button>
          )}
          {error && <p className="mt-2 text-xs text-caution">{error}</p>}
        </div>
      </div>

      {/* Results */}
      <div>
        <div ref={mapWrap} className="mb-4 scroll-mt-[78px]">
          <SearchMap areas={ranked} selected={selected} onSelect={select} />
          <p className="mt-1.5 text-[11px] text-muted">
            All {ranked.length} matches are on the map (grouped into clusters when they overlap) —
            click a pin or a result for a quick look, then open the full page.
          </p>
        </div>
        <div className="mb-3.5 flex items-baseline justify-between">
          <div className="text-sm text-ink2">
            <span className="font-mono text-ink">{pool.length}</span> areas match your filters
          </div>
          <div className="hidden text-[13px] text-muted sm:block">Match = your weighting of the 5 indicators</div>
        </div>
        <div className="relative" style={{ height: ranked.length * ROW_H }}>
          {ranked.map((a, i) => {
            const isSel = selected?.area_id === a.area_id;
            return (
              <div
                key={a.area_id}
                className="absolute inset-x-0 transition-[top] duration-[550ms] ease-[cubic-bezier(.22,.61,.36,1)]"
                style={{ top: i * ROW_H, height: ROW_H - 14 }}
              >
                <div
                  role="button"
                  tabIndex={0}
                  aria-pressed={isSel}
                  onClick={() => select(a)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      select(a);
                    }
                  }}
                  className={`group flex h-full cursor-pointer items-center gap-4 rounded-[14px] border px-[18px] py-4 transition-colors ${
                    isSel ? "border-accent bg-accent-wash" : "border-rule2 bg-card hover:border-accent-line"
                  }`}
                >
                  <div className="w-[54px] flex-shrink-0 text-center">
                    <div className="font-mono text-xs text-muted">#{i + 1}</div>
                    <div className="font-mono text-[30px] font-medium leading-none text-ink">{fmtScore(a.match_score)}</div>
                    <div className="text-[10px] uppercase tracking-[.06em] text-muted">match</div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="font-display text-[23px] font-bold leading-[1.1] text-ink transition-colors group-hover:text-accent">
                      {a.area_name}
                    </div>
                    <div className="mt-0.5 text-[13px] text-muted">
                      {[a.local_authority_name, a.region].filter(Boolean).join(" · ")}
                      {a.official_rent_monthly_gbp != null && (
                        <>
                          {" · "}
                          <span className="font-mono text-ink2">{rentPerMonth(a.official_rent_monthly_gbp)}</span>
                        </>
                      )}
                    </div>
                    <div className="mt-[11px] flex flex-wrap gap-3.5">
                      {SLIDERS.map((s) => {
                        const v = a[s.key];
                        return (
                          <div key={s.key} className="min-w-[48px]">
                            <div className="mb-[3px] flex justify-between gap-1.5 text-[10px] text-muted">
                              <span>{s.abbr}</span>
                              <span className="font-mono text-ink2">{fmtScore(v)}</span>
                            </div>
                            <div className="h-1 w-full overflow-hidden rounded-[2px] bg-bar-track">
                              <div
                                className="h-full rounded-[2px]"
                                style={{ width: v == null ? 0 : `${v}%`, background: weights[s.key] >= 4 ? "var(--accent)" : "var(--bar)" }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  <Link
                    href={`/area/${areaSlug(a.area_id, a.area_name)}`}
                    onClick={(e) => e.stopPropagation()}
                    aria-label={`Open ${a.area_name} details`}
                    className="flex h-[38px] w-[38px] flex-shrink-0 cursor-pointer items-center justify-center self-center rounded-[8px] border border-rule2 bg-card2 text-ink transition-colors hover:border-accent hover:bg-accent hover:text-white"
                  >
                    →
                  </Link>
                </div>
              </div>
            );
          })}
          {ranked.length === 0 && !loading && (
            <p className="text-sm text-muted">No areas match those filters. Try widening the budget or regions.</p>
          )}
        </div>
      </div>
    </div>
  );
}
