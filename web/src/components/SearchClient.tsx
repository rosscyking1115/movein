"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import type { Area, ComponentKey, SearchResponse } from "@/lib/types";
import { reweight } from "@/lib/reweight";
import { areaSlug } from "@/lib/slug";
import { rentPerMonth, score as fmtScore } from "@/lib/format";

const SLIDERS: { key: ComponentKey; label: string; abbr: string }[] = [
  { key: "affordability_score", label: "Affordability", abbr: "Aff" },
  { key: "safety_score", label: "Lower crime", abbr: "Saf" },
  { key: "energy_score", label: "Energy efficiency", abbr: "Ene" },
  { key: "flood_score", label: "Flood resilience", abbr: "Flo" },
  { key: "convenience_score", label: "Getting around", abbr: "Get" },
];
const TAGS = ["Ignore", "Minor", "Some", "Matters", "High", "Top"];
const REGIONS = [
  "North East", "North West", "Yorkshire and The Humber", "East Midlands",
  "West Midlands", "East of England", "London", "South East", "South West", "Wales",
];

const DEFAULT_WEIGHTS: Record<ComponentKey, number> = {
  affordability_score: 3, safety_score: 3, energy_score: 3, flood_score: 2, convenience_score: 3,
};
const SHOWN = 40;
const ROW_H = 162;

export function SearchClient({
  initialAreas,
  initialRegions,
}: {
  initialAreas: Area[];
  initialRegions: string[];
}) {
  const [weights, setWeights] = useState<Record<ComponentKey, number>>(DEFAULT_WEIGHTS);
  const [regions, setRegions] = useState<string[]>(initialRegions);
  const [budget, setBudget] = useState(2200);
  const [pool, setPool] = useState<Area[]>(initialAreas);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const effective = useMemo(() => {
    const sum = Object.values(weights).reduce((a, b) => a + b, 0);
    if (sum > 0) return weights;
    return Object.fromEntries(SLIDERS.map((s) => [s.key, 1])) as Record<ComponentKey, number>;
  }, [weights]);

  const ranked = useMemo(() => reweight(pool, effective).slice(0, SHOWN), [pool, effective]);

  const applyFilters = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          weights: effective,
          regions: regions.length ? regions : null,
          max_rent: budget < 2200 ? budget : null,
          limit: 200,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? "Search failed.");
      setPool(((await res.json()) as SearchResponse).results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }, [effective, regions, budget]);

  const toggleRegion = (r: string) =>
    setRegions((p) => (p.includes(r) ? p.filter((x) => x !== r) : [...p, r]));

  return (
    <div className="grid items-start gap-[26px] lg:grid-cols-[minmax(0,300px)_minmax(0,1fr)]">
      {/* Controls */}
      <div className="rounded-[16px] border border-rule2 bg-card p-[22px] lg:sticky lg:top-[78px]">
        <div className="mb-[18px] font-mono text-[11px] uppercase tracking-[.12em] text-ink">Weight each indicator</div>
        {SLIDERS.map((s) => (
          <div key={s.key} className="mb-[18px]">
            <div className="mb-[7px] flex items-baseline justify-between">
              <label htmlFor={s.key} className="text-sm font-semibold text-ink">{s.label}</label>
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
          <div className="mb-2.5 text-xs uppercase tracking-[.06em] text-muted">Filters</div>
          <label htmlFor="budget" className="mb-1.5 block text-[13px] text-ink2">
            Max 2-bed rent · <span className="font-mono text-ink">{budget >= 2200 ? "£2,200+" : `£${budget}`}</span>
          </label>
          <input
            id="budget"
            type="range"
            min={600}
            max={2200}
            step={50}
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            className="mb-4 h-6 w-full cursor-pointer accent-[var(--accent)]"
          />
          <div className="mb-2 text-[13px] text-ink2">Region</div>
          <div className="flex flex-wrap gap-1.5">
            {REGIONS.map((r) => {
              const active = regions.includes(r);
              return (
                <button
                  key={r}
                  type="button"
                  onClick={() => toggleRegion(r)}
                  className={`rounded-full border px-2.5 py-1 text-xs ${
                    active ? "border-accent bg-accent text-white" : "border-rule2 text-ink2 hover:text-ink"
                  }`}
                >
                  {r}
                </button>
              );
            })}
          </div>
          <button
            type="button"
            onClick={applyFilters}
            disabled={loading}
            className="mt-4 w-full rounded-[8px] bg-accent px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
          >
            {loading ? "Updating…" : "Apply filters"}
          </button>
          {error && <p className="mt-2 text-xs text-caution">{error}</p>}
        </div>
      </div>

      {/* Results */}
      <div>
        <div className="mb-3.5 flex items-baseline justify-between">
          <div className="text-sm text-ink2">
            <span className="font-mono text-ink">{pool.length}</span> areas match your filters
          </div>
          <div className="hidden text-[13px] text-muted sm:block">Match = your weighting of the 5 indicators</div>
        </div>
        <div className="relative" style={{ height: ranked.length * ROW_H }}>
          {ranked.map((a, i) => (
            <div
              key={a.area_id}
              className="absolute inset-x-0 transition-[top] duration-[550ms] ease-[cubic-bezier(.22,.61,.36,1)]"
              style={{ top: i * ROW_H, height: ROW_H - 14 }}
            >
              <div className="flex h-full items-center gap-4 rounded-[14px] border border-rule2 bg-card px-[18px] py-4">
                <div className="w-[54px] flex-shrink-0 text-center">
                  <div className="font-mono text-xs text-muted">#{i + 1}</div>
                  <div className="font-mono text-[30px] font-medium leading-none text-ink">{fmtScore(a.match_score)}</div>
                  <div className="text-[10px] uppercase tracking-[.06em] text-muted">match</div>
                </div>
                <div className="min-w-0 flex-1">
                  <Link
                    href={`/area/${areaSlug(a.area_id, a.area_name)}`}
                    className="font-display text-[23px] font-bold leading-[1.1] text-ink hover:text-accent"
                  >
                    {a.area_name}
                  </Link>
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
                              style={{
                                width: v == null ? 0 : `${v}%`,
                                background: weights[s.key] >= 4 ? "var(--accent)" : "var(--bar)",
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
                <Link
                  href={`/area/${areaSlug(a.area_id, a.area_name)}`}
                  aria-label={`Open ${a.area_name}`}
                  className="flex h-[38px] w-[38px] flex-shrink-0 items-center justify-center self-center rounded-[8px] border border-rule2 bg-card2 text-ink"
                >
                  →
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
